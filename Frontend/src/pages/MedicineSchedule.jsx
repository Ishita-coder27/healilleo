import DashboardLayout from "../components/DashboardLayout";

function MedicineSchedule() {
  return (
    <DashboardLayout
      title="Medicine Schedule"
      subtitle="AI-generated dosage & reminders"
    >
      <div className="card">💊 Paracetamol<br />Morning – 1 Tablet</div>
      <div className="card">💊 Vitamin D<br />Afternoon – 1 Capsule</div>
      <div className="card">💊 Cough Syrup<br />Night – 10ml</div>
    </DashboardLayout>
  );
}

export default MedicineSchedule;

