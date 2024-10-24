// make sure to add to login-open to body classlist for preventing overflow
// need to implement user sign out (html too)
import {useState} from 'react';

// style imports
import '../src/styles/login.css';
import '../src/styles/homepage.css';
import './img/profile.jpeg';

const Login = () => {
  // set up use state for displaying login popup
  const [loginPopup, setLoginPopup] = useState(false);

  // allow popup to be toggleable
  const toggleLoginPopup = () => {
    setLoginPopup(!loginPopup);
  };

  return (
    <div>
      <div className="profile-box">
        <a onClick={toggleLoginPopup}>
          <img src="img/profile.jpeg" alt="Profile Icon" />
        </a>
      </div>
      <div className="login-popup" id="popup">
        <div className="login-popup-content">
          <span className="close-popup">&times;</span>
          <form action="" className="form-container">
            <h2>Login</h2>
            <label for="username"><b>Username</b></label>
            <input type="text" placeholder="Enter username" name="username" required />
            <label for="password"><b>Password</b></label>
            <input type="password" placeholder="Enter password" name="password" required />
            <div className="option-container">
              <button type="submit" className="login-btn">Login</button>
              <a className="new-account" id="create-new-account">Register</a>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Login;