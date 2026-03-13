import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import axios from 'axios';
import { Upload, FileText, MessageCircle, BarChart3, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import Dropzone from 'react-dropzone';

// Backend API base URL - dev: localhost:8000, prod: adjust
const API_BASE = 'http://localhost:8000/api';

function MedicalReports() {
  const [samples, setSamples] = useState([]);
  const [selectedSample, setSelectedSample] = useState('');
  const [file, setFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [recommendations, setRecommendations] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatting, setChatting] = useState(false);
  const [status, setStatus] = useState('');
  const [activeTab, setActiveTab] = useState('summary');

  const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || '8000';

  const loadSamples = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/reports/samples`);
      setSamples(res.data.samples || []);
      if (res.data.samples.length > 0) {
        setSelectedSample(res.data.samples[0]);
      }
    } catch (err) {
      setStatus('Backend not running? Start: cd backend && uvicorn app.main:app --reload');
      console.error('Samples load error:', err);
    }
  }, []);

  const analyze = useCallback(async () => {
    if (!selectedSample && !file) return setStatus('Select sample or upload PDF');
    setAnalyzing(true);
    setStatus('');

    try {
      const formData = new FormData();
      if (file) {
        formData.append('pdf_file', file);
      } else {
        formData.append('sample_name', selectedSample);
      }

      const res = await axios.post(`${API_BASE}/reports/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setReportData(res.data);
      setChatHistory([]);

      // Get recommendations
      const recRes = await axios.post(`${API_BASE}/reports/recommendations`, res.data);
      setRecommendations(recRes.data);

      setStatus(`Analyzed \`${res.data.report_name}\`. Ask questions in chat below.`);
    } catch (err) {
      setStatus(`Analysis failed: ${err.response?.data?.detail || err.message}`);
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  }, [selectedSample, file]);

  const sendChat = async () => {
    if (!chatInput.trim() || !reportData) return;
    const question = chatInput.trim();
    setChatting(true);
    setChatInput('');

    const userMsg = { role: 'user', content: question };
    const tempHistory = [...chatHistory, userMsg];

    try {
      const res = await axios.post(`${API_BASE}/reports/chat`, {
        question,
        report_data: reportData
      });
      const aiMsg = { role: 'assistant', content: res.data.answer };
      setChatHistory(tempHistory.concat(aiMsg));
    } catch (err) {
      const errorMsg = { role: 'assistant', content: `Error: ${err.message}` };
      setChatHistory(tempHistory.concat(errorMsg));
    } finally {
      setChatting(false);
    }
  };

  useEffect(() => {
    loadSamples();
  }, [loadSamples]);

  const summaryMarkdown = reportData ? `
## Report Overview
**Source Report:** ${reportData.report_name}

**Patient:** ${reportData.patient_info.patient_name || 'Unknown'}
**Age:** ${reportData.patient_info.age || 'Unknown'}
**Gender:** ${reportData.patient_info.gender || 'Unknown'}
**Report Date:** ${reportData.patient_info.report_date || 'Unknown'}
**Extraction Method:** ${reportData.pdf_method}

### Extraction Stats
- Total vitals found: ${reportData.stats.total}
- Normal values: ${reportData.stats.normal}
- Abnormal values: ${reportData.stats.abnormal}

### Sample of Extracted Vitals
${reportData.vitals_detailed.slice(0,8).map(v => 
  `- ${v.name}: ${v.value}${v.unit ? ' ' + v.unit : ''}${v.status !== 'Unknown' ? ' [' + v.status + ']' : ''}`
).join('\n')}
  `.trim() : '';

  return (
    <DashboardLayout title="Medical Reports AI Analyzer" subtitle="Upload or select sample PDF → extract vitals → ask AI">
      <div className="max-w-6xl mx-auto p-6 space-y-8">
        {/* Hero */}
        <div className="hero bg-gradient-to-r from-blue-900 via-blue-800 to-indigo-900 rounded-3xl p-8 text-white text-center shadow-2xl">
          <h1 className="text-4xl font-bold mb-4">AI Health Report Assistant</h1>
          <p className="text-xl opacity-90 mb-8 max-w-2xl mx-auto">
            Select a sample report or upload your PDF. AI extracts all vitals, then ask context-aware questions.
          </p>
          <div className="status bg-blue-500/20 border border-blue-400 rounded-xl p-4 max-w-md mx-auto">
            {status || 'Ready – choose report to analyze'}
          </div>
        </div>

        {/* Controls */}
        <div className="controls bg-white/50 backdrop-blur-xl rounded-2xl p-6 shadow-lg border">
          <div className="grid md:grid-cols-3 gap-6 items-end">
            <div>
              <label className="block text-sm font-medium mb-2">Sample Reports</label>
              <select 
                value={selectedSample} 
                onChange={(e) => setSelectedSample(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={analyzing}
              >
                <option value="">Select sample...</option>
                {samples.map(name => <option key={name}>{name}</option>)}
              </select>
            </div>

            <Dropzone 
              multiple={false} 
              accept={{ 'application/pdf': ['.pdf'] }}
              onDrop={accepted => setFile(accepted[0])}
              disabled={analyzing}
            >
              {({ getRootProps, getInputProps, isDragActive }) => (
                <div 
                  {...getRootProps()} 
                  className="p-6 border-2 border-dashed border-gray-300 rounded-xl hover:border-blue-400 transition-colors cursor-pointer md:col-span-2 bg-gray-50 hover:bg-blue-50"
                >
                  <input {...getInputProps()} />
                  <div className="text-center">
                    <Upload className="mx-auto h-12 w-12 text-gray-400 mb-2" />
                    <p className="font-medium text-gray-900">
                      {file ? file.name : 'Upload your PDF report'}
                    </p>
                    <p className="text-sm text-gray-500">
                      {isDragActive ? 'Drop PDF here...' : 'Click or drag PDF (max 20MB)'}
                    </p>
                  </div>
                </div>
              )}
            </Dropzone>
          </div>

          <div className="flex gap-4 mt-6">
            <button
              onClick={analyze}
              disabled={analyzing || (!selectedSample && !file)}
              className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold py-4 px-8 rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 flex items-center justify-center gap-2 text-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {analyzing ? (
                <>
                  <div className="animate-spin rounded-full h-6 w-6 border-2 border-white border-t-transparent" />
                  Analyzing...
                </>
              ) : (
                <>
                  <FileText className="h-6 w-6" />
                  Analyze Report
                </>
              )}
            </button>
            <button
              onClick={() => { setReportData(null); setFile(null); setSelectedSample(''); setChatHistory([]); }}
              className="px-8 py-4 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold rounded-xl transition-colors"
              disabled={analyzing}
            >
              Clear
            </button>
          </div>
        </div>

        {reportData && (
          <>
            {/* Tabs */}
            <div className="tabs bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="flex border-b">
                <button onClick={() => setActiveTab('summary')} className={`flex-1 py-4 px-6 font-medium transition-colors ${activeTab === 'summary' ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}>
                  📋 Summary
                </button>
                <button onClick={() => setActiveTab('data')} className={`flex-1 py-4 px-6 font-medium transition-colors ${activeTab === 'data' ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}>
                  📊
                  <span className="ml-1">${reportData.stats.total} Vitals</span>
                </button>
                <button onClick={() => setActiveTab('recommendations')} className={`flex-1 py-4 px-6 font-medium transition-colors ${activeTab === 'data' ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}>
                  💡 Recommendations
                </button>
              </div>

              {/* Tab Panels */}
              <div className="p-8">
                {activeTab === 'summary' && (
                  <div>
                    <ReactMarkdown className="prose prose-lg max-w-none prose-headings:font-bold prose-p:leading-relaxed">
                      {summaryMarkdown}
                    </ReactMarkdown>
                  </div>
                )}

                {activeTab === 'data' && (
                  <div>
                    <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                      <BarChart3 />
                      Extracted Vitals ({reportData.vitals_detailed.length})
                    </h3>
                    <div className="grid gap-4">
                      {reportData.vitals_detailed.map((vital, i) => (
                        <div key={i} className="flex items-center gap-4 p-4 border rounded-xl hover:shadow-md transition-shadow bg-gradient-to-r from-gray-50 to-gray-100">
                          <div className={`w-3 h-3 rounded-full ${vital.status === 'Normal' ? 'bg-green-500' : 'bg-orange-500'}`} />
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-gray-900 truncate">{vital.name}</div>
                            <div className="text-sm text-gray-500 capitalize">{vital.category}</div>
                          </div>
                          <div className="text-2xl font-bold text-gray-900">
                            {vital.value} <span className="text-lg font-normal text-gray-500">{vital.unit}</span>
                          </div>
                          <div className="text-sm font-medium px-3 py-1 rounded-full bg-gray-100">
                            {vital.status}
                          </div>
                          <div className="text-xs text-gray-500 bg-white px-2 py-1 rounded">
                            {vital.method}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'recommendations' && (
                  <div>
                    <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                      <Bot />
                      AI Health Recommendations
                    </h3>
                    <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-8 prose prose-lg max-w-none">
                      <ReactMarkdown>{recommendations}</ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* ASK AI Chat */}
            <div className="chat-section bg-gradient-to-b from-slate-50 to-white rounded-2xl shadow-lg border overflow-hidden">
              <div className="p-8 border-b bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                <h3 className="text-2xl font-bold flex items-center gap-3">
                  <MessageCircle className="h-8 w-8" />
                  Ask AI About This Report
                </h3>
                <p className="opacity-90 mt-1">AI keeps the analyzed report in context for accurate answers</p>
              </div>

              <div className="p-6 space-y-4">
                <div className="chat-messages max-h-96 overflow-y-auto space-y-4 pr-4">
                  {chatHistory.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : ''}`}>
                      <div className={`max-w-2xl p-4 rounded-2xl ${msg.role === 'user' ? 'bg-blue-600 text-white ml-auto' : 'bg-white shadow border'}`}>
                        <p>{msg.content}</p>
                      </div>
                    </div>
                  ))}
                  {chatting && (
                    <div className="flex">
                      <div className="max-w-2xl p-4 rounded-2xl bg-white shadow border">
                        <div className="typing-indicator">
                          <div className="dot"></div>
                          <div className="dot"></div>
                          <div className="dot"></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex gap-3 pt-4 border-t">
                  <input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendChat()}
                    placeholder="Ask about abnormal vitals, diet advice, etc..."
                    className="flex-1 p-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    disabled={chatting || !reportData}
                  />
                  <button
                    onClick={sendChat}
                    disabled={chatting || !chatInput.trim() || !reportData}
                    className="px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl hover:shadow-lg transition-all disabled:opacity-50 flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    Send
                  </button>
                </div>
              </div>
            </div>
          </>
        )}

        {!reportData && (
          <div className="text-center py-20 bg-white/50 backdrop-blur-xl rounded-2xl shadow-lg">
            <FileText className="h-24 w-24 text-gray-400 mx-auto mb-6" />
            <h3 className="text-2xl font-bold text-gray-700 mb-2">No report analyzed yet</h3>
            <p className="text-lg text-gray-500 max-w-md mx-auto">
              Select a sample report or upload your PDF above to get started. AI will extract all vitals automatically.
            </p>
          </div>
        )}
      </div>

      <style jsx>{`
        .typing-indicator {
          display: flex;
          gap: 4px;
        }
        .typing-indicator .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #ccc;
          animation: typing 1.4s infinite;
        }
        .typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-10px); opacity: 1; }
        }
        .prose h3 { color: #1f2937; }
        .prose strong { color: #111827; }
      `}</style>
    </DashboardLayout>
  );
}

export default MedicalReports;

