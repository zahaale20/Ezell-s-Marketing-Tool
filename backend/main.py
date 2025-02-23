import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from typing import List

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set.")
client = OpenAI(api_key=api_key)

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StoryRequest(BaseModel):
    story: str

@app.post("/extract_key_ideas")
async def extract_key_ideas(request: StoryRequest):
    story_text = request.story.strip()
    if not story_text:
        return {"key_ideas": []}

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
                    "content": (
                        f"Story:\n{story_text}\n\n"
                        "Extract exactly three **unique storytelling-based key insights** as JSON: "
                        "[\"Lesson 1\", \"Lesson 2\", \"Lesson 3\"]."
                    )
                }
            ],
            temperature=0.5
        )

        # Check if response contains choices
        if not response.choices or len(response.choices) == 0:
            raise ValueError("No choices returned from OpenAI API")

        raw_content = response.choices[0].message.content.strip()

        # Validate JSON structure
        try:
            insights_list = json.loads(raw_content)
            if not isinstance(insights_list, list) or len(insights_list) != 3:
                raise ValueError("Response format invalid: Expected a list of exactly 3 insights.")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON received: {raw_content}")

    except Exception as e:
        print(f"Error generating key ideas: {str(e)}")  # Log the error
        return {"error": f"Failed to generate key ideas: {str(e)}"}

    return {"key_ideas": insights_list}

class PostRequest(BaseModel):
    key_ideas: List[str]

class PostRequest(BaseModel):
    story: str
    key_ideas: List[str]

from typing import List

class PostRequest(BaseModel):
    story: str
    key_ideas: List[str]

@app.post("/generate_texts")
async def generate_texts(request: PostRequest):
    if not request.story.strip() or not request.key_ideas:
        raise HTTPException(status_code=400, detail="Both story and key_ideas must be provided.")

    key_ideas = request.key_ideas
    full_story = request.story.strip()

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert social media strategist. Generate **engaging, platform-optimized** posts "
                        "for Instagram, Twitter (X), and Facebook based on the provided key ideas. "
                        "Ensure each post is **narrative-driven, educational, and optimized for engagement**.\n\n"
                        "⚠ **IMPORTANT:** Each post must be **based on exactly one unique fact** from the key ideas.\n\n"
                        "Return JSON format:\n"
                        "[\n"
                        "  { \"instagram\": \"(Post 1)\", \"twitter\": \"(Post 1)\", \"facebook\": \"(Post 1)\" },\n"
                        "  { \"instagram\": \"(Post 2)\", \"twitter\": \"(Post 2)\", \"facebook\": \"(Post 2)\" },\n"
                        "  { \"instagram\": \"(Post 3)\", \"twitter\": \"(Post 3)\", \"facebook\": \"(Post 3)\" }\n"
                        "]"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Story:\n{full_story}\n\n"
                        f"Key Ideas:\n{json.dumps(key_ideas)}\n\n"
                        "Generate **distinct social media posts** based on the story and each key idea."
                    )
                }
            ],
            temperature=0.8
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating social media posts: {e}")

    try:
        raw_content = response.choices[0].message.content.strip()
        posts = json.loads(raw_content)

        if not isinstance(posts, list) or len(posts) != len(key_ideas):
            raise ValueError("Invalid response format: Expected list of posts matching key ideas.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing response: {e}")

    return {"posts": posts}




class ImageRequest(BaseModel):
    key_idea: str
    platform: str
    post_text: str

@app.post("/generate_images")
async def generate_images(request: ImageRequest):
    key_idea = request.key_idea.strip()
    platform = request.platform.strip()
    post_text = request.post_text.strip()

    if not key_idea or not post_text:
        raise HTTPException(status_code=400, detail="Key idea and post text are required.")

    platform_descriptions = {
        "Instagram": "Visually stunning, high-contrast, and storytelling-driven. Optimized for engagement.",
        "Twitter": "Minimalist but impactful, delivering a clear and bold message.",
        "Facebook": "Professional, educational, and focused on community-driven engagement."
    }

    prompt = (
        f"Generate a compelling AI-generated image that visually represents the idea '{key_idea}'. "
        f"The image should be optimized for {platform}, following these design principles: {platform_descriptions.get(platform, '')}.\n\n"
        f"Context from social media post: \"{post_text}\" \n\n"
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
        print(f"Generated Image URL for {key_idea} - {platform}: {image_url}")  # Log the image URL
        return {"image_url": image_url}

    except Exception as e:
        print(f"Error generating image for {key_idea} - {platform}: {str(e)}")  # Log the error
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")



# Run with `uvicorn main:app --reload --port 8000`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
import json
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from typing import List

app = FastAPI()

# ✅ CORS Configuration (Allows frontend to communicate with backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Request Models
class StoryRequest(BaseModel):
    story: str

class PostRequest(BaseModel):
    story: str
    key_ideas: List[str]

class ImageRequest(BaseModel):
    key_idea: str
    platform: str
    post_text: str

# ✅ Helper Function to Initialize OpenAI Client
def get_openai_client(api_key: str):
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing OpenAI client: {str(e)}")

# ✅ Extract Key Ideas
@app.post("/extract_key_ideas")
async def extract_key_ideas(request: StoryRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    api_key = authorization.split("Bearer ")[1]
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    try:
        client = get_openai_client(api_key)  # ✅ Use user-provided API key
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
                    "content": f"Story:\n{request.story}\n\nExtract exactly three **unique key insights** as JSON."
                }
            ],
            temperature=0.5
        )

        if not response.choices:
            raise ValueError("No response from OpenAI API")

        raw_content = response.choices[0].message.content.strip()
        insights_list = json.loads(raw_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

    return {"key_ideas": insights_list}

# ✅ Generate Text-Based Social Media Posts
@app.post("/generate_texts")
async def generate_texts(request: PostRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    api_key = authorization.split("Bearer ")[1]
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    if not request.story.strip() or not request.key_ideas:
        raise HTTPException(status_code=400, detail="Both story and key_ideas must be provided.")

    try:
        client = get_openai_client(api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert social media strategist. Generate **engaging, platform-optimized** posts "
                        "for Instagram, Twitter (X), and Facebook based on the provided key ideas. "
                        "Ensure each post is **narrative-driven, educational, and optimized for engagement**.\n\n"
                        "⚠ **IMPORTANT:** Each post must be **based on exactly one unique fact** from the key ideas.\n\n"
                        "Return JSON format:\n"
                        "[\n"
                        "  { \"instagram\": \"(Post 1)\", \"twitter\": \"(Post 1)\", \"facebook\": \"(Post 1)\" },\n"
                        "  { \"instagram\": \"(Post 2)\", \"twitter\": \"(Post 2)\", \"facebook\": \"(Post 2)\" },\n"
                        "  { \"instagram\": \"(Post 3)\", \"twitter\": \"(Post 3)\", \"facebook\": \"(Post 3)\" }\n"
                        "]"
                    )
                },
                {
                    "role": "user",
                    "content": f"Story:\n{request.story}\n\nKey Ideas:\n{json.dumps(request.key_ideas)}\n\nGenerate posts."
                }
            ],
            temperature=0.8
        )

        if not response.choices:
            raise ValueError("No response from OpenAI API")

        raw_content = response.choices[0].message.content.strip()
        posts = json.loads(raw_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

    return {"posts": posts}

# ✅ Generate AI-Generated Images
@app.post("/generate_images")
async def generate_images(request: ImageRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    api_key = authorization.split("Bearer ")[1]
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    if not request.key_idea or not request.post_text:
        raise HTTPException(status_code=400, detail="Key idea and post text are required.")

    platform_descriptions = {
        "Instagram": "Visually stunning, high-contrast, and storytelling-driven. Optimized for engagement.",
        "Twitter": "Minimalist but impactful, delivering a clear and bold message.",
        "Facebook": "Professional, educational, and focused on community-driven engagement."
    }

    prompt = (
        f"Generate a compelling AI-generated image that visually represents the idea '{request.key_idea}'. "
        f"The image should be optimized for {request.platform}, following these design principles: {platform_descriptions.get(request.platform, '')}.\n\n"
        f"Context from social media post: \"{request.post_text}\" \n\n"
        f"The image must align with this message and provide a visually engaging representation. "
        f"**DO NOT** generate abstract or irrelevant visuals. Ensure the image directly connects to both the key idea and the generated post."
        f"**DO NOT** add any text in the actual images."
    )

    try:
        client = get_openai_client(api_key)
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

# ✅ Run API Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
