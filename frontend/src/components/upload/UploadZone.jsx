import { useRef,useState } from "react";


function UploadZone() {
    const fileInputRef = useRef(null);
    const [selectedFile, setSelectedFile] = useState(null);
  return (
   <div>
    <h2>Upload file</h2>
      <p >Drag & drop your blood report or choose a file.</p>
       <input href={fileInputRef} type="file"/>
       <button >Choose File</button>
    </div>
      
  );
}


export default UploadZone;