import { useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";

function App() {
  const [count, setCount] = useState(0);

  return (
    <>
      <div>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>AutoGen UI</h1>
      <div className="card">
        <input type='text' className="input"/>
      
      </div>
      <div className="card">
        <button>Submit</button>
      </div>
      <p className="read-the-docs">
        Hello in AutoGen
        <br />
        The next generation of AutoGPT
      </p>
    </>
  );
}

export default App;
