import DashboardLayout from "../components/DashboardLayout";

function DietExercise() {
  return (
    <DashboardLayout
      title="Diet & Exercise"
      subtitle="Personalized AI fitness & nutrition plan"
    >
      <div className="card">🥗 Breakfast<br />Oats + Fruits</div>
      <div className="card">🍱 Lunch<br />Brown Rice + Vegetables</div>
      <div className="card">🏃 Exercise<br />30 min Jogging</div>
      <div className="card">🧘 Evening<br />15 min Yoga</div>
    </DashboardLayout>
  );
}

export default DietExercise;

