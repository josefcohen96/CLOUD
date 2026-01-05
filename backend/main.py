@app.post("/analyze")
async def analyze_meal_endpoint(user_id: int = Form(...), file: UploadFile = File(...)):
    temp_filename = f"/tmp/{file.filename}"
    if os.name == 'nt': temp_filename = file.filename 

    try:
        print(f"[DEBUG] Received file `{file.filename}` for user `{user_id}`.")
        
        # שמירת הקובץ זמנית בשרת/למבדה
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"[DEBUG] File `{temp_filename}` written successfully.")
        
        # 1. העלאה ל-S3 וקבלת URL
        image_url = upload_to_s3(temp_filename, file.filename)
        if not image_url:
            print("[ERROR] Failed to upload file to S3.")
            raise HTTPException(status_code=500, detail="Failed to upload file to S3.")
        print(f"[DEBUG] Uploaded file to S3. URL: {image_url}")
        
        # 2. שליחה לניתוח AI (כולל ה-URL לשמירה ב-DB)
        print("[DEBUG] Starting AI analysis.")
        analysis_result = analyze_food_image(temp_filename, user_id=user_id, image_url=image_url)
        
        if not analysis_result: 
            print("[ERROR] AI analysis failed.")
            raise HTTPException(status_code=500, detail="Analysis failed")
        print(f"[DEBUG] AI analysis completed successfully. Result: {analysis_result}")
            
        return {"status": "success", "data": analysis_result, "image_url": image_url}

    except Exception as e:
        print(f"[EXCEPTION ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during analysis.")
        
    finally:
        try:
            if os.path.exists(temp_filename): 
                os.remove(temp_filename)
                print(f"[DEBUG] Temporary file `{temp_filename}` removed successfully.")
        except Exception as cleanup_error:
            print(f"[WARNING] Failed to clean up temporary file `{temp_filename}`: {cleanup_error}")