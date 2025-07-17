import os #環境変数
import time #待機処理
import pandas as pd #csv
from googleapiclient.discovery import build #youtubeのapi呼び出し
from googleapiclient.errors import HttpError #api呼び出しエラー処理
from dotenv import load_dotenv #envファイルから呼び出し

def init_youtube_api(): #youtubr api利用
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY") #apiの情報を直接書かない
    return build("youtube", "v3", developerKey=api_key)

def fetch_comments(query, max_videos=3, max_comments_per_video=50): #コメント取得
    youtube = init_youtube_api()
    comments = []

    try:
        search_results = youtube.search().list( #動画検索
            q=query, part="id", type="video", maxResults=max_videos
        ).execute()
    except HttpError as e:
        print(f"検索エラー: {e}")
        return comments

    for item in search_results["items"]:
        video_id = item["id"]["videoId"]
        try:
            title_response = youtube.videos().list( #タイトル取得
                part="snippet", id=video_id
            ).execute()
            title = title_response["items"][0]["snippet"]["title"]
        except:
            title = "Unknown"

        print(f"{title} のコメント取得中...")

        next_page = None
        count = 0
        while count < max_comments_per_video:
            try:
                response = youtube.commentThreads().list( #コメント取得
                    part="snippet",
                    videoId=video_id,
                    maxResults=min(100, max_comments_per_video - count),
                    pageToken=next_page,
                    textFormat="plainText"
                ).execute()
            except HttpError as e:
                print(f"コメント取得エラー: {e}")
                break

            for c in response["items"]:
                snippet = c["snippet"]["topLevelComment"]["snippet"]
                comments.append({ #コメント情報抽出
                    "videoId": video_id,
                    "videoTitle": title,
                    "author": snippet["authorDisplayName"],
                    "text": snippet["textDisplay"],
                    "likeCount": snippet["likeCount"],
                    "publishedAt": snippet["publishedAt"]
                })
                count += 1
                if count >= max_comments_per_video:
                    break

            next_page = response.get("nextPageToken")
            if not next_page:
                break
            time.sleep(0.5) #api制限対策

    return comments

def save_to_csv(data, filename): #データをcsvで
    pd.DataFrame(data).to_csv(filename, index=False, encoding='utf-8-sig')
    print(f" {filename} に保存完了（{len(data)}件）")

def main():
    comments = fetch_comments("人工知能", max_videos=3, max_comments_per_video=50)
    if comments:
        save_to_csv(comments, "youtube_ai_comment.csv")
    else:
        print("コメントが取得できませんでした。")

if __name__ == "__main__":
    main()