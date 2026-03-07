import DashboardLayout from "../components/DashboardLayout";

function MedicalReports() {
  return (
    <DashboardLayout
      title="Medical Reports"
      subtitle="AI-analyzed medical documents"
    >
      <div className="card">📄 Blood Test Report<br />Status: Normal</div>
      <div className="card">📄 X-Ray Summary<br />AI Result: Clear</div>
      <div className="card">📄 Sugar Levels<br />AI Risk: Low</div>
    </DashboardLayout>
  );
}

export default MedicalReports;

