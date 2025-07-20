import json
import pandas as pd
from openai import OpenAI
from app.analyzer import get_recent_posts, find_hot_topics, add_impact_score, find_most_impactful_posts
from app.core.config import settings

# Initialize OpenAI Client
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_llm_response(prompt: str, is_json=False):
    """A helper function to call the OpenAI API."""
    print(f"Generating content with prompt: {prompt[:80]}...")
    try:
        response_format = {"type": "json_object"} if is_json else {"type": "text"}
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format=response_format,
            temperature=0.5
        )
        content = response.choices[0].message.content
        return json.loads(content) if is_json else content
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return None

def get_image_url(post):
    """Safely get the first image URL from a post."""
    images = post.get('images')
    return images[0] if images and isinstance(images, list) and len(images) > 0 else None

def generate_fallback_post(posts_df: pd.DataFrame):
    """Generates a LinkedIn post based on the most impactful posts of the day."""
    print("No topics found. Generating fallback post based on impact...")
    
    # 1. Get top 3-5 impactful posts
    impactful_posts = find_most_impactful_posts(posts_df, top_n=3)
    if impactful_posts.empty:
        print("No impactful posts to summarize.")
        return

    # 2. Prepare content for the LLM prompt
    post_summaries = []
    for _, post in impactful_posts.iterrows():
        author_name = post.get('author', {}).get('name', 'Unknown')
        content = post.get('content', '')
        post_summaries.append(f"- Post by {author_name}: {content}")

    combined_content = "\n".join(post_summaries)

    # 3. Generate the LinkedIn post text
    final_prompt = (
        "You are a professional social media manager for AIGORA, an AI news platform. "
        "No specific hot topics were identified today. Instead, write a general summary post about the most significant AI news from the last 24 hours based on the provided top posts. "
        "Mention the key developments and companies involved. Keep it formal but engaging, with no symbols. End with a call to action to find all sources on the AIGORA news portal.\n\n"
        f"TOP POSTS:\n{combined_content}"
    )
    final_post_text = generate_llm_response(final_prompt)

    # 4. Select top image and references
    top_image_url = get_image_url(impactful_posts.iloc[0])
    references = impactful_posts['post_url'].tolist()

    # 5. Structure and save the final output
    final_output = {
        "post_text": final_post_text,
        "top_image_url": top_image_url,
        "references": references
    }
    
    output_path = "fallback_linkedin_post.json"
    with open(output_path, "w") as f:
        json.dump(final_output, f, indent=2)

    print(f"\n✅ Successfully generated fallback LinkedIn post and saved to {output_path}")
    print(json.dumps(final_output, indent=2))


def generate_topic_post():
    """Finds hot topics via clustering, summarizes them, and generates a LinkedIn post."""
    posts_df = get_recent_posts()
    if posts_df.empty:
        print("No recent posts found to generate a topic post.")
        return

    posts_df = add_impact_score(posts_df)
    topic_groups = find_hot_topics(posts_df)

    if not topic_groups or len(topic_groups) == 0:
        generate_fallback_post(posts_df)
        return

    sorted_topics = sorted(topic_groups, key=lambda x: len(x[1]), reverse=True)[:3]
    
    topic_outputs = []
    for topic_id, group_df in sorted_topics:
        representative_post = group_df.sort_values(by='impact_score', ascending=False).iloc[0]
        combined_content = "\n\n---\n\n".join(group_df['content'].dropna())
        
        prompt = (
            "You are a tech journalist. Summarize this topic in a concise, engaging paragraph (2-3 sentences). "
            "Focus on the core message and its significance. Do not use symbols or bullet points.\n\n"
            f"POSTS:\n{combined_content}"
        )
        topic_summary = generate_llm_response(prompt)
        
        topic_outputs.append({
            "summary": topic_summary,
            "image": get_image_url(representative_post),
            "links": group_df['post_url'].tolist()
        })
    
    top_image_url = topic_outputs[0]['image']
    summaries_for_final_post = [t['summary'] for t in topic_outputs if t['summary']]

    # --- CORRECTED PROMPT CONSTRUCTION ---
    # First, join the summaries into a single block of text
    formatted_summaries = "\n- ".join(summaries_for_final_post)

    # Then, insert that block into the final prompt
    final_prompt = (
        "You are a professional social media manager for AIGORA, an AI news platform. "
        "Write a formal yet engaging LinkedIn post that synthesizes the following topic summaries into a cohesive narrative about the day's trends in AI. "
        "Do not use emojis or special symbols. End with a call to action to find all sources on the AIGORA news portal.\n\n"
        "TOPIC SUMMARIES:\n"
        f"- {formatted_summaries}"
    )
    final_post_text = generate_llm_response(final_prompt)
    
    all_links = [link for topic in topic_outputs for link in topic['links']]
    final_output = {
        "post_text": final_post_text,
        "top_image_url": top_image_url,
        "references": list(set(all_links))
    }
    
    output_path = "output/topic_linkedin_post.json"
    with open(output_path, "w") as f:
        json.dump(final_output, f, indent=2)

    print(f"\n✅ Successfully generated topic-based LinkedIn post and saved to {output_path}")
    print(json.dumps(final_output, indent=2))

if __name__ == "__main__":
    generate_topic_post()