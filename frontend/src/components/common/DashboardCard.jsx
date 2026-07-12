function DashboardCard({title, description, icon}) {
  return (
    <div className="bg-slate-900 text-white p-6 rounded-xl shadow-md hover:shadow-xl transition cursor-pointer">
      <h2>{title}</h2>
      <p>{description}</p>
      <div>{icon}</div>
    
    </div>
  );
}


export default DashboardCard;