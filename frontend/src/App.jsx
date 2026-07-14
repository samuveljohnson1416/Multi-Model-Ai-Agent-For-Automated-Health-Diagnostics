import './App.css'


import { Routes,Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard.jsx';
import Chat from './pages/Chat.jsx';
import Report from './pages/Report.jsx';
import Analysis from './pages/Analysis.jsx';
import Upload from './pages/Upload.jsx';
import Settings from './pages/Settings.jsx';

function App() {
   return(
      <Routes>
      <Route path='/' element={<Dashboard/>} />
      <Route path='/chat' element={<Chat/>} />
      <Route path='/report' element={<Report/>} />
      <Route path='/analysis' element={<Analysis/>} />
      <Route path='/upload' element={<Upload/>} />
      <Route path='/settings' element={<Settings/>} />

    </Routes>
  ) ;
}


export default App;