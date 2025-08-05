import pandas as pd
from opensearchpy import OpenSearch
import hdbscan
import numpy as np
from datetime import datetime, timedelta
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from app.core.config import settings

# --- Initialize Clients & Models ---
opsearch_client = OpenSearch(
    hosts=[{'host': settings.OPENSEARCH_HOST, 'port': 9200}],
    use_ssl=False, verify_certs=False
)
# BERTopic requires the embedding model to be available
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# --- Main Functions ---
def get_recent_posts(days_back: int = 30):
    """Fetches posts from the last N days from OpenSearch."""
    print(f"🔍 Fetching posts from the last {days_back} day(s)...")
    time_window = datetime.utcnow() - timedelta(days=days_back)

    query = {
        "query": {
            "bool": {
                "must": [
                    {"exists": {"field": "content_vector"}},
                    {"range": {"published_at": {"gte": time_window.isoformat()}}}
                ]
            }
        },
        "size": 1000
    }

    response = opsearch_client.search(index="posts", body=query)
    hits = response['hits']['hits']
    print(f"📄 Found {len(hits)} posts.")
    return pd.DataFrame([h['_source'] for h in hits])

def find_hot_topics(df: pd.DataFrame, algorithm: str = "hdbscan"):
    """Clusters posts to find topics using the specified algorithm."""
    print(f"🧠 Clustering posts with {algorithm} to find hot topics...")
    if df.empty or 'content_vector' not in df.columns:
        return None, None

    vectors = np.array(df['content_vector'].tolist())
    docs = df['content'].tolist()

    if algorithm == "bertopic":
        topic_model = BERTopic(embedding_model=embedding_model, min_topic_size=2)
        topics, _ = topic_model.fit_transform(docs, embeddings=vectors)
        df['topic_id'] = topics
        topic_info = topic_model.get_topic_info()
        print(f"📊 BERTopic found {len(topic_info) - 1} potential topics.")
    else: # Default to HDBSCAN
        clusterer = hdbscan.HDBSCAN(min_cluster_size=2, min_samples=1, metric='euclidean')
        labels = clusterer.fit_predict(vectors)
        df['topic_id'] = labels
        topic_info = None # HDBSCAN doesn't provide topic info directly

    # Filter out noise (-1) and group posts by topic
    topic_groups = df[df['topic_id'] != -1].groupby('topic_id')

    if not topic_info:
         print(f"📊 HDBSCAN found {len(topic_groups)} potential topics.")

    return topic_groups, topic_info

# --- NEW REFACTORED FUNCTIONS ---
def add_impact_score(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates and adds a weighted 'impact_score' column to the DataFrame."""
    if df.empty:
        return df

    df_copy = df.copy()
    df_copy['likes'] = df_copy['engagement'].apply(lambda x: x.get('likes', 0) if isinstance(x, dict) else 0)
    df_copy['comments'] = df_copy['engagement'].apply(lambda x: x.get('comments', 0) if isinstance(x, dict) else 0)
    df_copy['shares'] = df_copy['engagement'].apply(lambda x: x.get('shares', 0) if isinstance(x, dict) else 0)
    df_copy['impact_score'] = (df_copy['likes'] * 1) + (df_copy['comments'] * 2) + (df_copy['shares'] * 3)
    
    return df_copy

def find_most_impactful_posts(df: pd.DataFrame, top_n=3):
    """Finds the most impactful posts based on a weighted engagement score."""
    print("💥 Finding most impactful posts...")
    if df.empty:
        return pd.DataFrame()

    # Create a deep copy to avoid SettingWithCopyWarning
    df_copy = df.copy()

    # Extract engagement data safely
    df_copy['likes'] = df_copy['engagement'].apply(lambda x: x.get('likes', 0) if isinstance(x, dict) else 0)
    df_copy['comments'] = df_copy['engagement'].apply(lambda x: x.get('comments', 0) if isinstance(x, dict) else 0)
    df_copy['shares'] = df_copy['engagement'].apply(lambda x: x.get('shares', 0) if isinstance(x, dict) else 0)

    # Calculate impact score
    df_copy['impact_score'] = (df_copy['likes'] * 1) + (df_copy['comments'] * 2) + (df_copy['shares'] * 3)
    
    return df_copy.sort_values(by='impact_score', ascending=False).head(top_n)

def generate_llm_summary(topic_groups, impactful_posts):
    """Uses OpenAI to generate a final digest."""
    print("✍️ Generating topic titles with OpenAI...")

    # 1. Generate a title for each topic
    topic_summaries = []
    for topic_id, group in topic_groups:
        combined_content = "\n\n---\n\n".join(group['content'].dropna().head(5))
        prompt = f"Summarize the key theme of the following posts in a short, 3-5 word topic title:\n\n{combined_content}"

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=15
        )
        title = response.choices[0].message.content.strip().replace('"', '')
        topic_summaries.append(f"## {title}\n- Based on {len(group)} related posts.")

    # --- NEW: Print topics as soon as they are generated ---
    print("\n--- 📝 Topics Found ---")
    for summary in topic_summaries:
        print(summary)
    print("---------------------\n")
    # ----------------------------------------------------

    print("✍️ Generating final digest with OpenAI...")
    # 2. Format the impactful posts
    impact_summary = ["# Top Posts by Impact"]
    for _, post in impactful_posts.iterrows():
        author_name = post.get('author', {}).get('name', 'Unknown Author')
        content_preview = (post.get('content') or '')[:200]
        likes = post.get('engagement', {}).get('likes', 0)
        comments = post.get('engagement', {}).get('comments', 0)
        impact_summary.append(f"### {author_name}\n> {content_preview}...\n- Likes: {likes}, Comments: {comments}")

    # 3. Combine everything for the final digest
    topic_section = "\n".join(topic_summaries)
    impact_section = "\n".join(impact_summary)

    final_prompt = (
        "You are an expert AI news analyst. Write a concise and insightful daily digest based on the following information. "
        "Start with a brief, engaging introductory paragraph.\n\n"
        "# Hot Topics Today\n"
        f"{topic_section}\n\n"
        f"{impact_section}"
    )

    final_response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0.5,
        max_tokens=1024
    )
    return final_response.choices[0].message.content

def run_analysis():
    """Main function to run the full analysis pipeline."""
    posts_df = get_recent_posts()
    if posts_df.empty:
        print("No recent posts found to analyze.")
        return

    topic_groups = find_hot_topics(posts_df)
    impactful_posts = find_most_impactful_posts(posts_df)
    digest = generate_llm_summary(topic_groups, impactful_posts)

    print("\n--- 🌟 Generated Daily Digest 🌟 ---\n")
    print(digest)


if __name__ == "__main__":
    run_analysis()