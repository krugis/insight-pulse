import json
import pandas as pd
from openai import OpenAI
from app.analyzer import get_recent_posts, find_hot_topics, find_most_impactful_posts, add_impact_score
from app.core.config import settings

# Initialize OpenAI Client
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_content_for_section(prompt: str, model="gpt-4o", is_json=True):
    """A helper function to call the OpenAI API and parse the response."""
    print(f"Generating content with prompt: {prompt[:80]}...")
    try:
        response_format = {"type": "json_object"} if is_json else {"type": "text"}
        response = openai_client.chat.completions.create(
            model=model,
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

def generate_newspaper_content():
    """Fetches, analyzes, and generates all content for the newspaper portal."""
    
    posts_df = get_recent_posts()
    if len(posts_df) < 5:
        print("Not enough recent posts to generate a full newspaper. Need at least 5.")
        return

    # --- UPDATED LOGIC: Calculate score first! ---
    posts_df = add_impact_score(posts_df)

    # --- 1. Analyze all posts first ---
    topic_groups = find_hot_topics(posts_df)
    impactful_posts = find_most_impactful_posts(posts_df, top_n=10)

    # --- 2. Strategically Select Posts for Each Section ---
    main_story_post = impactful_posts.iloc[0]
    secondary_story_posts = impactful_posts.iloc[1:3]
    
    # Find the largest topic cluster
    largest_topic_id = max(topic_groups.groups, key=lambda k: len(topic_groups.get_group(k)))
    largest_topic_df = topic_groups.get_group(largest_topic_id)
    
    # Select the most impactful post within the largest topic for the "Highlight"
    highlight_post = largest_topic_df.sort_values(by='impact_score', ascending=False).iloc[0]

    # --- 3. Generate Content for Each Section ---
    
    # Main Story
    main_story_prompt = f"Write a 'Main Story' for a newspaper front page based on this post. Create a long, dramatic `headline` and a detailed `paragraph` (100 words). Respond with a JSON object with 'headline' and 'paragraph' keys.\n\nPOST: {main_story_post['content']}"
    main_story = generate_content_for_section(main_story_prompt)
    if main_story:
        main_story['image'] = get_image_url(main_story_post)
        main_story['reference_link'] = main_story_post['post_url']

    # Secondary Stories
    secondary_stories_prompt = f"Write 2 short news briefs. Each needs a `headline` and a one-sentence `summary`. Respond with a JSON object with a 'stories' key holding an array of 2 objects.\n\nPOST 1: {secondary_story_posts.iloc[0]['content']}\n\nPOST 2: {secondary_story_posts.iloc[1]['content']}"
    secondary_stories_data = generate_content_for_section(secondary_stories_prompt).get('stories', [])
    for i, story in enumerate(secondary_stories_data):
        post = secondary_story_posts.iloc[i]
        story['image'] = get_image_url(post)
        story['reference_link'] = post['post_url']
        
    # Sidebar
    sidebar_prompt = f"Generate a 'Highlight of the Week' with a `headline` and `summary` based on the Highlight Post. Also generate 4 short, one-sentence headlines for 'In Other News' from the Other Posts. Respond with a JSON object with a `highlight` object and an `other_news` array.\n\nHIGHLIGHT POST: {highlight_post['content']}\n\nOTHER POSTS:\n{posts_df.head(10)['content'].str.cat(sep=' | ')}"
    sidebar_content = generate_content_for_section(sidebar_prompt)
    if sidebar_content and 'highlight' in sidebar_content:
        sidebar_content['highlight']['image'] = get_image_url(highlight_post)
        sidebar_content['highlight']['reference_link'] = highlight_post['post_url']
    
    # News Ticker
    ticker_prompt = f"Write 3 very short, urgent, breaking-news style headlines based on these posts. Respond with a JSON object with a `headlines` array.\n\nPOSTS:\n{impactful_posts.head(3)['content'].str.cat(sep=' | ')}"
    news_ticker = generate_content_for_section(ticker_prompt)

    # --- 4. Assemble Final JSON ---
    final_content = {
        "news_ticker": news_ticker,
        "main_story": main_story,
        "secondary_stories": secondary_stories_data,
        "sidebar": sidebar_content
    }

    output_path = "output/newspaper_content.json"
    with open(output_path, "w") as f:
        json.dump(final_content, f, indent=2)

    print(f"\n✅ Successfully generated newspaper content and saved to {output_path}")
    print(json.dumps(final_content, indent=2))

if __name__ == "__main__":
    generate_newspaper_content()