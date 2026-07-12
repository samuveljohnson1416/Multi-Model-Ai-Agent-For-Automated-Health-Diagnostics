import Layout from "../components/layouts/Layout";
import DashboardCard from "../components/common/DashboardCard";
const dashboardCards=[{
  id:1,
    title:"Blood parameters",
    description:"Upload your blood report image for AI-powered analysisAI Analysis",
    icon:"...",
},{
    id:2,
    title:"AI recommendations",
    description:"Upload your blood report image for AI-powered analysisAI Analysis",
    icon:"...",
},{
    id:3,
    title:"Chat history",
    description:"Upload your blood report image for AI-powered analysisAI Analysis",
    icon:"...",
},{
    id:4,
    title:"Medical alerts",
    description:"Upload your blood report image for AI-powered analysisAI Analysis",
    icon:"...",
},
]

function Dashboard() {
  return (
    <Layout>
      <h1 className="text-3xl font-bold">
        Dashboard
      </h1>
      {dashboardCards.map((card)=> (
      <DashboardCard key={card.id}
        title={card.title}
        description={card.description}
        icon={card.icon}
        onClick={() => navigate('/dashboard')}
        />))}
        
    </Layout>
  
);
}

export default Dashboard;