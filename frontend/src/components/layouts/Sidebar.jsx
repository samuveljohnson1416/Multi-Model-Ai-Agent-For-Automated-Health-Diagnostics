import navigationItems from "../../data/navigation";

import { useNavigate } from "react-router-dom";

function Sidebar() {
  const navigate = useNavigate();
  return (
    <aside className="flex flex-col grid justify-center items-center gap-2">
      <h1>SideBar</h1>
      {navigationItems.filter((item) =>item.showInSidebar).map((item)=>(
      <button key={item.id}onClick={() => navigate(item.route)} >  
        {item.title}{item.icon}
      </button>

    ))}
    </aside>
  );
}

    
    
export default Sidebar;