import requests
import logging
import time
from typing import Optional, Dict, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class FacebookAPI:
    BASE_URL = "https://graph.facebook.com/v18.0/"

    def __init__(self, access_token: str, max_retries: int = 1):
        self.access_token = access_token
        self.max_retries = max_retries

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = urljoin(self.BASE_URL, endpoint)
        if "params" in kwargs:
            kwargs["params"]["access_token"] = self.access_token
        else:
            kwargs["params"] = {"access_token": self.access_token}

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return {"success": True, "data": response.json()}
            except requests.exceptions.RequestException as e:
                logger.error(f"[Attempt {attempt+1}] Facebook API error: {e}")
                if attempt < self.max_retries:
                    time.sleep(1)
                else:
                    content = response.content if 'response' in locals() else None
                    return {"success": False, "error": str(e), "response": content}






    # --- Posts ---
    def post_text(self, message: str, page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"{page_id}/feed" if page_id else "me/feed"
        return self._make_request("POST", endpoint, data={"message": message})
            
            
            
    def post_link(self, message: str, link: str, published: bool = True, scheduled_publish_time: Optional[int] = None, page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"{page_id}/feed" if page_id else "me/feed"
        data = {
            "message": message,
            "link": link
        }
        
        if published:
            data["published"] = "true"
        else:
            data["published"] = "false"
            if not scheduled_publish_time:
                return {"success": False, "error": "scheduled_publish_time required when published=False"}
            data["scheduled_publish_time"] = scheduled_publish_time
        
        return self._make_request("POST", endpoint, data=data)
    
        """_summary_Si vous choisissez la valeur false, ajoutez scheduled_publish_time avec la date dans l’un des formats suivants :

            - Un nombre entier au format UNIX [en secondes] (par exemple 1530432000)
            - Une chaîne ISO 8061 (par exemple 2018-09-01T10:15:30+01:00)
            - N’importe quelle chaîne qui peut être traitée par le strtotime() de PHP (par exemple +2 weeks, tomorrow)
        
        NB: La date de publication doit être comprise entre 10 minutes et 30 jours après la date de la requête API.
        """



    def post_image(self, image_url: str, page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"{page_id}/photos" if page_id else "me/photos"
        return self._make_request("POST", endpoint, data={"url": image_url})

    
    
    def post_media(self, video_path: str, file_type: str, title: str = "", description: str = "", page_id: Optional[str] = None, chunk_size: int = 10*1024*1024) -> Dict[str, Any]:
        import os
        import time
        
        if not os.path.exists(video_path):
            return {"success": False, "error": f"File not found: {video_path}"}
        
        file_name = os.path.basename(video_path)
        file_size = os.path.getsize(video_path)
        file_type = file_type
        
        
        #Step 1: Start upload session
        print("Step 1: Starting upload session...")
        app_id = "1523680902101746"
        import_session_endpoint = f"{app_id}/uploads"
        
        session_result = self._make_request(
            "POST", 
            import_session_endpoint,
            params={
                "file_name": file_name,
                "file_length": file_size,
                "file_type": file_type
            }
        )
        
        if not session_result["success"]:
            return session_result
        
        upload_session_id = session_result["data"].get("id")
        if not upload_session_id:
            return {"success": False, "error": "No upload session ID received"}
        
        print(f"Upload session ID: {upload_session_id}")
        print(f"File size: {file_size} bytes")
        
        #Step 2: Upload file data
        print("Step 2: Uploading file data...")
        
        upload_url = f"https://graph.facebook.com/v18.0/{upload_session_id}"
        print(f"Upload URL: {upload_url}")
        
        file_offset = 0
        chunk_number = 0
        file_handle = None
        
        try:
            with open(video_path, 'rb') as video_file:
                while file_offset < file_size:
                    chunk = video_file.read(chunk_size)
                    if not chunk:
                        break
                    
                    chunk_number += 1
                    print(f"Uploading chunk {chunk_number} (offset: {file_offset}, size: {len(chunk)} bytes)")
                    
                    headers = {
                        "Authorization": f"OAuth {self.access_token}",
                        "file_offset": str(file_offset),
                        "Content-Type": "application/octet-stream"
                    }
                    
                    response = requests.post(
                        upload_url,
                        headers=headers,
                        data=chunk
                    )
                    
                    if response.status_code == 413:
                        chunk_size = chunk_size // 2
                        print(f"Chunk too large, reducing to {chunk_size} bytes")
                        video_file.seek(file_offset)
                        chunk_number -= 1
                        continue
                    
                    if response.status_code == 400:
                        print(f"400 Error details: {response.text}")
                        return {"success": False, "error": f"Upload failed: {response.text}"}
                    
                    response.raise_for_status()
                    
                    try:
                        result_data = response.json()
                        if "h" in result_data:
                            #take the first one
                            raw_handle = result_data['h']
                            if '\n' in raw_handle:
                                file_handle = raw_handle.split('\n')[0].strip()
                                print(f"Multiple file handles received, using first one: {file_handle}")
                            else:
                                file_handle = raw_handle
                                print(f"Single file handle received: {file_handle}")
                            break
                    except:
                        pass
                    
                    file_offset += len(chunk)
                    print(f"Chunk {chunk_number} uploaded successfully, new offset: {file_offset}")
            

            if not file_handle:
                print("ALL CHUNKS UPLOADED SUCCESSFULLY - Getting file handle......")
                
                time.sleep(3)
                
                headers = {
                    "Authorization": f"OAuth {self.access_token}"
                }
                
                for attempt in range(3):
                    try:
                        final_res = requests.get(upload_url, headers=headers)
                        final_res.raise_for_status()
                        upload_result = final_res.json()
                        
                        raw_handle = upload_result.get("h")
                        if raw_handle:
                            #take the first one
                            if '\n' in raw_handle:
                                file_handle = raw_handle.split('\n')[0].strip()
                                print(f"Multiple file handles received, using first one: {file_handle}")
                            else:
                                file_handle = raw_handle
                                print(f"Single file handle received: {file_handle}")
                            break
                        else:
                            print(f"Attempt {attempt + 1}: No file handle in response, waiting...")
                            time.sleep(2)
                    except Exception as e:
                        print(f"Attempt {attempt + 1}: Error getting file handle: {e}")
                        time.sleep(2)
                        
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {str(e)}"}
        
        if not file_handle:
            return {"success": False, "error": "No file handle received"}
        
        print(f"Final file handle: {file_handle}")
        
        #Step 3: Publish the video
        print("Step 3: Publishing video...")
        if file_type == "video/mp4":
            endpoint = f"{page_id}/videos" if page_id else "me/videos"
            
            original_base_url = self.BASE_URL
            self.BASE_URL = "https://graph-video.facebook.com/v18.0/"
            
            publish_data = {
                "title": title,
                "description": description,
                "fbuploader_video_file_chunk": file_handle
            }
        else:
            endpoint = f"{page_id}/photos"
            original_base_url = self.BASE_URL
            self.BASE_URL = "https://graph.facebook.com/v18.0/"
            
            publish_data = {
                "message": description,
                "fbuploader_video_file_chunk": file_handle,
                "published": "true"
            }
        


        
        try:
            publish_result = self._make_request("POST", endpoint, data=publish_data)
        finally:
            self.BASE_URL = original_base_url
        
        return publish_result
    
    
    
    def delete_post(self, post_id: str):
        endpoint = f"{post_id}"
        return self._make_request("DELETE", endpoint)






    # --- Get Posts ---
    #def get_posts(self, limit: int = 10, page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"{page_id}/posts" if page_id else "me/posts"
        params = {"limit": limit, "fields": "id,message,created_time,attachments"}
        return self._make_request("GET", endpoint, params=params)
    
    
    
    def get_posts(self, page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"{page_id}/feed" if page_id else "me/feed"
        return self._make_request("GET", endpoint)




    # --- Post Stats ---
    def get_post_stats(self, post_id: str) -> Dict[str, Any]:
        params = {
            "fields": "id,likes.summary(true),comments.summary(true),shares"
        }
        return self._make_request("GET", post_id, params=params)

    # --- Comments ---
    def get_comments(self, post_id: str, limit: int = 10) -> Dict[str, Any]:
        endpoint = f"{post_id}/comments"
        params = {"limit": limit, "fields": "id,from,message,created_time"}
        return self._make_request("GET", endpoint, params=params)

    def reply_to_comment(self, comment_id: str, message: str) -> Dict[str, Any]:
        endpoint = f"{comment_id}/comments"
        return self._make_request("POST", endpoint, data={"message": message})

    # --- Comment Moderation ---
    def hide_comment(self, comment_id: str) -> Dict[str, Any]:
        endpoint = comment_id
        return self._make_request("POST", endpoint, data={"is_hidden": "true"})

    def delete_comment(self, comment_id: str) -> Dict[str, Any]:
        return self._make_request("DELETE", comment_id)

    # --- Page Info ---
    def get_page_info(self, page_id: Optional[str] = None) -> Dict[str, Any]:
        endpoint = page_id if page_id else "me"
        params = {"fields": "id,name,followers_count,fan_count"}
        return self._make_request("GET", endpoint, params=params)
