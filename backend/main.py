from fastapi import FastAPI, UploadFile, File

app=FastAPI()

@app.post("/upload")
async def upload_file(file:UploadFile=File(...)):
    return{
        "filename":file.filename,
        # pyrefly: ignore [parse-error]
        "content_type":file.content_type
    }