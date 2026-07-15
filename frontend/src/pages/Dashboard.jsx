import Layout from "../components/layouts/Layout";
import DashboardCard from "../components/common/DashboardCard";
import {useNavigate } from "react-router-dom";
import navigationItems from "../data/navigation.jsx";


function Dashboard() {
  const navigate = useNavigate();
  return (
    <Layout>
      <h1 className="text-3xl font-bold">
        Dashboard
      </h1>
      {navigationItems.filter(
        (item) => item.showOnDashboard)
        .map((item)=> (
      <DashboardCard key={item.id}
        title={item.title}
        description={item.description}
        icon={item.icon}
        
        
        onClick={() => navigate(item.route)}
        />))}
        
    </Layout>
  
);
}

export default Dashboard;