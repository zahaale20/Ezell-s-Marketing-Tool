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

  // API usage states
  const [usageKeyIdeas, setUsageKeyIdeas] = useState({ tokens: 0, cost: 0 });
  const [usagePosts, setUsagePosts] = useState({ tokens: 0, cost: 0 });
  const [usageImages, setUsageImages] = useState({ tokens: 0, cost: 0 });
  const [loadingUsage, setLoadingUsage] = useState(false);
  
  // Fetch usage per section
  const fetchUsageStats = async (section, startTime) => {
    try {
      const response = await fetch(`http://localhost:8000/get_api_usage?section=${section}`, {
        method: "GET",
        headers: { Authorization: `Bearer ${apiKey}` },
      });
  
      if (!response.ok) throw new Error(`Failed to fetch API usage for ${section}`);
  
      const data = await response.json();
      const endTime = new Date().getTime();
      const runtime = (endTime - startTime) / 1000; // Convert to seconds
  
      if (section === "key_ideas") setUsageKeyIdeas({ ...data, runtime });
      if (section === "texts") setUsagePosts({ ...data, runtime });
      if (section === "images") setUsageImages({ ...data, runtime });
  
    } catch (error) {
      console.error(`Error fetching usage stats for ${section}:`, error);
      alert(`Something went wrong fetching API usage for ${section}.`);
    }
  };
  

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
    if (!story.trim()) {
      alert("Please enter a story.");
      return;
    }
    if (!apiKey.trim()) {
      alert("Please enter your OpenAI API key.");
      return;
    }
  
    setLoadingIdeas(true);
    const startTime = new Date().getTime();
  
    try {
      const response = await fetch("http://localhost:8000/extract_key_ideas", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${apiKey.trim()}`,  // ✅ Ensure no extra spaces
        },
        body: JSON.stringify({ story }),
      });
  
      if (!response.ok) {
        const errorMessage = await response.json();
        throw new Error(errorMessage.detail || "Failed to extract key ideas");
      }
  
      const data = await response.json();
      setKeyIdeas(data.key_ideas);
    } catch (error) {
      console.error("Error extracting ideas:", error);
      alert(error.message);
    } finally {
      fetchUsageStats("key_ideas", startTime);
      setLoadingIdeas(false);
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
    const startTime = new Date().getTime();
  
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
  
      console.log("Generated Posts Response:", data);
  
      if (!data.posts || !Array.isArray(data.posts)) {
        throw new Error("Invalid API response format: 'posts' must be an array.");
      }
  
      // 🔥 Ensure the posts are mapped correctly to keyIdeas
      const mappedPosts = keyIdeas.map((idea, index) => ({
        keyIdea: idea,
        instagram: data.posts[index]?.instagram || "",
        twitter: data.posts[index]?.twitter || "",
        facebook: data.posts[index]?.facebook || "",
      }));
  
      setPosts(mappedPosts);
    } catch (error) {
      console.error("Error generating texts:", error);
      alert("Something went wrong generating posts.");
    } finally {
      fetchUsageStats("texts", startTime);
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
    const startTime = new Date().getTime();
  
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
              "Authorization": `Bearer ${apiKey}`
            },
            body: JSON.stringify({ 
              key_ideas: keyIdea,
              platform, 
              post_text: postText 
            }),
          });
  
          if (!response.ok) throw new Error(`Failed to generate image for ${platform}`);
  
          const data = await response.json();
          console.log(`Generated Image URL for ${platform}:`, data.image_url);
  
          setImages((prevImages) => ({
            ...prevImages,
            [`${keyIdea}-${platform}`]: data.image_url,
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
  
    fetchUsageStats("images", startTime);
    setLoadingImages(false);
  };
  

  return (
    <div className="home-container">
      <div className="landing-box">
        <div className="text-section">
          <div className="post-output">
            <h1 style={{marginBottom: "60px"}}>TRANSFORM <span className="highlight">YOUR STORY</span> INTO SOCIAL MEDIA CONTENT</h1>
            <h2 className="output-title">Enter Your OpenAI API Key</h2>
            <input
              type="password"
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
          <div className="post-output">
            <h2 className="output-title">Share Your Story</h2>
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
            <h2 className="output-title">Extracted Key Ideas</h2>

            <div className="table-container">
              <table className="post-table">
                <thead>
                  <tr>
                    <th>Key Idea</th>
                  </tr>
                </thead>
                <tbody>
                  {(keyIdeas || []).map((idea, index) => (
                    <tr key={index}>
                      <td>{idea || "-"}</td>
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
            <h2 className="output-title">Generated Social Media Posts - Text</h2>

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
                  {(keyIdeas || []).map((idea, index) => (
                    <tr key={index}>
                      <td>{idea}</td>
                      <td>{posts?.[index]?.instagram || "-"}</td>
                      <td>{posts?.[index]?.twitter || "-"}</td>
                      <td>{posts?.[index]?.facebook || "-"}</td>
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
                  {(keyIdeas || []).map((idea, index) => (
                    <tr key={index}>
                      <td>{idea}</td>
                      {["Instagram", "Twitter", "Facebook"].map((platform) => {
                        const imageKey = `${idea}-${platform}`;
                        return (
                          <td key={platform}>
                            {imagesLoading?.[imageKey] ? (
                              <img src={love} alt="Loading" className="spinner-img rotate" />
                            ) : (
                              images?.[imageKey] ? (
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

          <div className="post-output">
            <h2 className="output-title">Final API Usage Summary</h2>
            
            <div className="usage-stats-container">
              <div className="usage-card">
                <img src={sunny} alt="Runtime Icon" className="usage-icon" />
                <div className="usage-info">
                  <div className="usage-label">Total Runtime</div>
                  <div className="usage-value">{(usageKeyIdeas.runtime + usagePosts.runtime).toFixed(2)} sec</div>
                </div>
              </div>

              <div className="usage-card">
                <img src={friedChicken} alt="Tokens Icon" className="usage-icon" />
                <div className="usage-info">
                  <div className="usage-label">Total Tokens</div>
                  <div className="usage-value">{usageKeyIdeas.tokens + usagePosts.tokens}</div>
                </div>
              </div>

              <div className="usage-card">
                <img src={bun} alt="Cost Icon" className="usage-icon" />
                <div className="usage-info">
                  <div className="usage-label">Total Cost</div>
                  <div className="usage-value">
                    ${(usageKeyIdeas.cost + usagePosts.cost).toFixed(4)}
                  </div>
                </div>
              </div>
            </div>
          </div>


          <div className="post-output">
            <div className="feature-placeholder">
              <h2>📲 Integrate Social Media APIs, Selenium or Find Alternative Solution</h2>
              <p>This feature is not developed yet. The system would at this point automate post publishing to Instagram, X, and Facebook.</p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
  

export default Home;
