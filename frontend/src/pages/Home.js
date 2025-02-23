import React, { useState, useEffect } from "react";
import sunny from "../assets/sunny.png";
import friedChicken from "../assets/fried-chicken.png";
import bun from "../assets/bun.png";
import love from "../assets/love.png";
import "./Home.css";

const Home = () => {
  const [apiKey, setApiKey] = useState("");
  const [story, setStory] = useState("");
  const [keyIdeas, setKeyIdeas] = useState([]);
  const [posts, setPosts] = useState([]);
  const [images, setImages] = useState({});
  const [imagesLoading, setImagesLoading] = useState({});

  // Loading states
  const [loadingIdeas, setLoadingIdeas] = useState(false);
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [loadingImages, setLoadingImages] = useState(false);

  // Save API key when updated
  useEffect(() => {
    if (apiKey) {
      localStorage.setItem("openai_api_key", apiKey);
    } else {
      localStorage.removeItem("openai_api_key");
    }
  }, [apiKey]);

  // Clear API key from localStorage
  const clearApiKey = () => {
    setApiKey("");
    localStorage.removeItem("openai_api_key");
  };

  // Calls FastAPI endpoint to extract key ideas
  const handleExtractIdeas = async () => {
    if (!story.trim()) return;
    if (!apiKey.trim()) {
      alert("Please enter your OpenAI API key.");
      return;
    }

    setLoadingIdeas(true)

    try {
      const response = await fetch("http://localhost:8000/extract_key_ideas", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${apiKey}`,
        },
        body: JSON.stringify({ story }),
      });

      if (!response.ok) throw new Error("Failed to extract key ideas");
      const data = await response.json();
      setKeyIdeas(data.key_ideas);
    } catch (error) {
      console.error("Error extracting ideas:", error);
      alert("Something went wrong extracting key ideas.");
    } finally {
      setLoadingIdeas(false)
    }
  };

  // Calls FastAPI endpoint to generate social media posts
  const handleGenerateTexts = async () => {
    if (keyIdeas.length === 0) {
      alert("Extract key ideas first!");
      return;
    }
    if (!apiKey.trim()) {
      alert("Please enter your OpenAI API key.");
      return;
    }

    setLoadingPosts(true);
    try {
      const response = await fetch("http://localhost:8000/generate_texts", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${apiKey}`
        },
        body: JSON.stringify({ story: story.trim(), key_ideas: keyIdeas }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Error details:", errorData);
        throw new Error("Failed to generate posts");
      }

      const data = await response.json();
      setPosts(data.posts);
    } catch (error) {
      console.error("Error generating texts:", error);
      alert("Something went wrong generating posts.");
    } finally {
      setLoadingPosts(false);
    }
  };

  // Calls FastAPI endpoint to generate images
  const handleGenerateImages = async () => {
    if (keyIdeas.length === 0 || posts.length === 0) {
      alert("Generate key ideas and posts first!");
      return;
    }
  
    setLoadingImages(true);
  
    const newImagesLoading = {};
    keyIdeas.forEach((keyIdea) => {
      ["Instagram", "Twitter", "Facebook"].forEach((platform) => {
        newImagesLoading[`${keyIdea}-${platform}`] = true;
      });
    });
  
    setImagesLoading(newImagesLoading);
  
    for (const keyIdea of keyIdeas) {
      for (const platform of ["Instagram", "Twitter", "Facebook"]) {
        const postText = posts.find(post => post[platform.toLowerCase()])?.[platform.toLowerCase()] || keyIdea;
  
        try {
          const response = await fetch("http://localhost:8000/generate_images", {
            method: "POST",
            headers: { 
              "Content-Type": "application/json",
              "Authorization": `Bearer ${apiKey}`  // ✅ Ensure API key is sent
            },
            body: JSON.stringify({ key_idea: keyIdea, platform, post_text: postText }),
          });
  
          if (!response.ok) throw new Error(`Failed to generate image for ${platform}`);
  
          const data = await response.json();
          console.log(`Generated Image URL for ${platform}:`, data.image_url); // Debugging
  
          setImages((prevImages) => ({
            ...prevImages,
            [`${keyIdea}-${platform}`]: data.image_url, // Update state immediately
          }));
        } catch (error) {
          console.error(`Error generating image for ${platform}:`, error);
        } finally {
          setImagesLoading((prev) => ({
            ...prev,
            [`${keyIdea}-${platform}`]: false,
          }));
        }
      }
    }
  
    setLoadingImages(false);
  };
  
  

  const minimumFields = 3;

  return (
    <div className="home-container">
      <div className="landing-box">
        <div className="text-section">

          <div className="feature-placeholder">
            <h2>🔍 Integrate OpenAI Search to Find Relevant Facts</h2>
            <p>This feature is not developed yet. The system will automatically search for verified facts to enhance social media posts.</p>
          </div>

          <h1 className="output-title">Transform Your Story into Social Media Posts</h1>

          {/* API Key Input Section */}
          <div className="input-section">
            <input
              type="password" // ✅ Hides API key input
              className="api-key-input"
              placeholder="Enter OpenAI API Key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
            {apiKey && (
              <button className="submit-button" onClick={clearApiKey}>Clear Key</button>
            )}
          </div>

          {/* Story Input Section */}
          <div className="input-section">
            <textarea
              className="story-input"
              placeholder="Tell your story here..."
              value={story}
              onChange={(e) => setStory(e.target.value)}
            />
            <button className="submit-button" onClick={handleExtractIdeas} disabled={loadingIdeas}>
              {loadingIdeas ? <img src={sunny} alt="Loading" className="spinner-img rotate" /> : "Extract Key Ideas"}
            </button>
          </div>

          {/* Key Ideas Section */}
          <div className="post-output">
            <h2 className="output-title">Key Ideas</h2>

            <div className="table-container">
              <table className="post-table">
                <thead>
                  <tr>
                    <th>Key Idea</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.from({ length: Math.max(minimumFields, keyIdeas.length) }).map((_, index) => (
                    <tr key={index}>
                      <td>{keyIdeas[index] || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button className="submit-button" onClick={handleGenerateTexts} disabled={loadingPosts}>
              {loadingPosts ? <img src={friedChicken} alt="Loading" className="spinner-img rotate" /> : "Generate Texts"}
            </button>
          </div>

          {/* Generated Posts Section */}
          <div className="post-output">
            <h2 className="output-title">Generated Text Content</h2>

            <div className="table-container">
              <table className="post-table">
                <thead>
                  <tr>
                    <th>Key Idea</th>
                    <th>Instagram</th>
                    <th>X</th>
                    <th>Facebook</th>
                  </tr>
                </thead>
                <tbody>
                  {keyIdeas.map((idea, index) => (
                    <tr key={index}>
                      <td>{idea}</td>
                      <td>{posts[index]?.instagram || "-"}</td>
                      <td>{posts[index]?.twitter || "-"}</td>
                      <td>{posts[index]?.facebook || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button className="submit-button" onClick={handleGenerateImages} disabled={loadingImages}>
              {loadingImages ? <img src={bun} alt="Loading" className="spinner-img rotate" /> : "Generate Images"}
            </button>
          </div>

          {/* Image Generation Section */}
          <div className="image-generation">
            <h2 className="output-title">Generated Social Media Posts - Images</h2>
            <div className="table-container">
              <table className="post-table">
                <thead>
                  <tr>
                    <th>Key Idea</th>
                    <th>Instagram</th>
                    <th>X</th>
                    <th>Facebook</th>
                  </tr>
                </thead>
                <tbody>
                  {keyIdeas.map((idea, index) => (
                    <tr key={index}>
                      <td>{idea}</td>
                      {["Instagram", "Twitter", "Facebook"].map((platform) => {
                        const imageKey = `${idea}-${platform}`;
                        return (
                          <td key={platform}>
                            {imagesLoading[imageKey] ? (
                              <img src={love} alt="Loading" className="spinner-img rotate" />
                            ) : (
                              images[imageKey] ? (
                                <img src={images[imageKey]} alt={`${platform} visualization`} className="generated-image" />
                              ) : (
                                <p style={{ color: "red" }}>Failed to Load</p>
                              )
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>

              </table>
            </div>
          </div>

          <div className="feature-placeholder">
            <h2>📲 Integrate Social Media APIs (if possible) or use Selenium</h2>
            <p>This feature is not developed yet. The system will automate post publishing to Instagram, X, and Facebook.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
