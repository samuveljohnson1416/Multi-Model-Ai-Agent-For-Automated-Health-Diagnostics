import { useRef,useState } from "react";


function UploadZone() {
    const fileInputRef = useRef(null);
    const [selectedFile, setSelectedFile] = useState(null);
  return (
   <div>
    <h2>Upload file</h2>
      <p >Drag & drop your blood report or choose a file.</p>
       <input ref={fileInputRef} type="file" accept=".pdf,.png,.jpg,.jpeg" className="hidden" onChange={(event) => {
    setSelectedFile(event.target.files[0]);
}}/>
       <button disabled={selectedFile=null} onClick={() => fileInputRef.current.click()} >Choose File</button>
       {selectedFile
  ? <p>Selected: {selectedFile.name}</p>
  : <p>No file selected</p>
}
    </div>
      
  );
}


export default UploadZone;