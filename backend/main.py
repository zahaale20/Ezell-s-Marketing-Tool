import json
import time
from fastapi import FastAPI, HTTPException, Header, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from typing import List

app = FastAPI()

# CORS Configuration (Allows frontend to communicate with backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Usage Tracking (Dictionary to store usage stats)
api_usage = {
    "key_ideas": {"tokens": 0, "cost": 0, "calls": 0, "runtime": 0},
    "texts": {"tokens": 0, "cost": 0, "calls": 0, "runtime": 0},
    "images": {"tokens": 0, "cost": 0, "calls": 0, "runtime": 0},
}

# Request Models
class StoryRequest(BaseModel):
    story: str

class PostRequest(BaseModel):
    story: str
    key_ideas: List[str]

class ImageRequest(BaseModel):
    key_ideas: str
    platform: str
    post_text: str

# Helper Function to Initialize OpenAI Client
def get_openai_client(api_key: str):
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing OpenAI client: {str(e)}")

# Function to Update API Usage Stats
def update_api_usage(section: str, tokens_used: int = 0, cost: float = 0.0, runtime: float = 0.0):
    if section in api_usage:
        api_usage[section]["tokens"] += tokens_used if tokens_used else 0
        api_usage[section]["cost"] += cost if cost else 0.0
        api_usage[section]["calls"] += 1
        api_usage[section]["runtime"] += runtime if runtime else 0.0

# Get API Usage data
@app.get("/get_api_usage")
async def get_api_usage(section: str = Query(..., description="API section (key_ideas, texts, images)")):
    if section not in api_usage:
        raise HTTPException(status_code=400, detail="Invalid API usage section requested")
    return api_usage[section]

# Extract Key Ideas
@app.post("/extract_key_ideas")
async def extract_key_ideas(request: StoryRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    api_key = authorization.split("Bearer ")[1].strip()
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    client = get_openai_client(api_key)

    if not request.story.strip():
        raise HTTPException(status_code=400, detail="Story must be provided.")

    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a storytelling and content strategy expert. Extract exactly 3 **high-impact, unique insights** "
                        "from the user's story. The extracted insights must:\n"
                        "- Be **deep, narrative-driven, and educational**.\n"
                        "- Preserve the **emotional depth and core message** of the story.\n"
                        "- Be structured as **compelling takeaways** that audiences can **learn from and apply**.\n"
                        "- **DO NOT** summarize the story.\n"
                        "- **DO NOT** include generic, obvious takeaways.\n"
                        "- **DO NOT** include clichés, redundant phrases, or fluff.\n\n"
                        "Return only valid JSON in this format: [\"Insight 1\", \"Insight 2\", \"Insight 3\"]. No extra text."
                    )
                },
                {
                    "role": "user",
                    "content": f"Story:\n{request.story.strip()}\n\nExtract exactly three **unique key insights** as JSON."
                }
            ],
            temperature=0.5
        )

        if not response.choices:
            raise ValueError("No response from OpenAI API")

        raw_content = response.choices[0].message.content.strip()
        key_ideas = json.loads(raw_content)

        # ✅ Check if usage data exists before accessing it
        tokens_used = getattr(response.usage, "total_tokens", 0)
        estimated_cost = tokens_used * 0.000015  # Example cost calculation

        runtime = round(time.time() - start_time, 2)

        update_api_usage("key_ideas", tokens_used, estimated_cost, runtime)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

    return {"key_ideas": key_ideas, "tokens_used": tokens_used, "cost": estimated_cost, "runtime": runtime}

# Generate Text-Based Social Media Posts
@app.post("/generate_texts")
async def generate_texts(request: PostRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    api_key = authorization.split("Bearer ")[1]
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    client = get_openai_client(api_key)

    if not request.key_ideas or not request.story:
        raise HTTPException(status_code=400, detail="Key ideas and story are required.")

    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert social media strategist and a master of **emotional storytelling**.\n"
                        "Your goal is to create three posts (Instagram, Twitter/X, Facebook) that:\n\n"
                        "1. Focus on exactly one unique key idea per post.\n"
                        "2. Evoke **strong emotions** and utilize **pathos** to connect deeply with readers.\n"
                        "3. Incorporate **at least one** specific data point, quote, or detail from the story.\n"
                        "4. Are narrative-driven, educational, and optimized for engagement.\n"
                        "5. Avoid clichés, filler phrases, or generic statements.\n\n"
                        "### Example (emphasizing emotional depth):\n"
                        "Story: \"I battled crippling self-doubt for years until a simple act of kindness showed me my worth.\"\n"
                        "Key Ideas: [\"Self-Worth\", \"Kindness\", \"Resilience\"]\n\n"
                        "Sample Output (in valid JSON):\n"
                        "[\n"
                        "  {\n"
                        "    \"instagram\": \"Sometimes, a single kind word can dissolve years of doubt...\",\n"
                        "    \"twitter\": \"I used to feel invisible, until someone reminded me I mattered...\",\n"
                        "    \"facebook\": \"My self-worth was buried under negativity. One day, a gentle conversation changed everything...\"\n"
                        "  },\n"
                        "  ...\n"
                        "]\n\n"
                        "Each post should read like a **short heartfelt story**, revealing genuine feelings from the original user’s journey. "
                        "Make sure each platform's post is unique, well-formatted, and references **one detail** from the user story.\n\n"
                        "#### IMPORTANT:\n"
                        "- Return **only** valid JSON in the exact format: an array of three objects.\n"
                        "- **No** extra commentary or text outside the JSON.\n"
                        "- Include as many relevant data points as possible to build\n"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Story:\n{request.story.strip()}\n\n"
                        f"Key Ideas:\n{json.dumps(request.key_ideas)}\n\n"
                        "Generate exactly three social media posts—one per key idea—"
                        "with an emotionally compelling narrative for each platform (Instagram, Twitter, Facebook)."
                    )
                },
            ],
            # A moderate temperature for some creative flair, but not too high
            temperature=0.6,
        )


        if not response.choices:
            raise ValueError("No response from OpenAI API")

        raw_content = response.choices[0].message.content.strip()
        posts = json.loads(raw_content)

        tokens_used = response.usage.total_tokens
        estimated_cost = tokens_used * 0.000015  # Adjust to your cost model

        runtime = round(time.time() - start_time, 2)
        update_api_usage("texts", tokens_used, estimated_cost, runtime)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating posts: {str(e)}")

    return {"posts": posts, "tokens_used": tokens_used, "cost": estimated_cost, "runtime": runtime}

# Generate AI-Generated Images
@app.post("/generate_images")
async def generate_images(request: ImageRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    api_key = authorization.split("Bearer ")[1]
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    client = get_openai_client(api_key)  #  Initialize OpenAI client

    if not request.key_ideas or not request.post_text:
        raise HTTPException(status_code=400, detail="Key idea and post text are required.")


    platform_descriptions = {
        "Instagram": "Visually stunning, high-contrast, and storytelling-driven. Optimized for engagement.",
        "Twitter": "Minimalist but impactful, delivering a clear and bold message.",
        "Facebook": "Professional, educational, and focused on community-driven engagement."
    }

    prompt = (
        f"Generate a compelling AI-generated image that visually represents the idea '{request.key_ideas}'. "
        f"The image should be optimized for {request.platform}, following these design principles: {platform_descriptions.get(request.platform, '')}.\n\n"
        f"Context from social media post: \"{request.post_text}\" \n\n"
        f"The image must align with this message and provide a visually engaging representation. "
        f"**DO NOT** generate abstract or irrelevant visuals. Ensure the image directly connects to both the key idea and the generated post."
        f"**DO NOT** add any text in the actual images."
    )

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        return {"image_url": image_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

#  Run API Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
