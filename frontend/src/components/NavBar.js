import React from "react";
import "./NavBar.css";
import logo from "../assets/cooped-up.png";

const Navbar = () => {

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-logo">
          <img 
            src={logo} 
            alt="Logo" 
            className="navbar-logo-image" 
          />
        </div>
      </div>
    </nav>
  );
};

export default Navbar;