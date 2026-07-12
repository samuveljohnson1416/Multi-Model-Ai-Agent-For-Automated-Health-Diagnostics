import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
import Footer from "./Footer";

function Layout({ children }) {
    return (
        <div className="min-h-screen flex flex-col">
            <Navbar />

            <div className="flex flex-1">
                <Sidebar />

                <main className="flex-1 p-6">
                    {children}
                </main>
            </div>

            <Footer />
        </div>
    );
}

export default Layout;