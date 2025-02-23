import React from "react";
import { Routes, Route } from "react-router-dom";
import styled from "styled-components";

import NavBar from "./components/NavBar";
import Home from "./pages/Home";

// 🔥 Styled component for a fixed background
const BackgroundContainer = styled.div`
  position: fixed; /* Ensures background stays in place */
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #ff9800; /* Orange background */
  z-index: -1; /* Places it behind all content */
`;

function App() {
  return (
    <>
      <NavBar />
      <BackgroundContainer /> {/* Fixed Background */}
      <div style={{ zIndex: 3, position: "relative", width: "100%", minHeight: "100vh", overflowY: "auto" }}>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </div>
    </>
  );
}

export default App;
