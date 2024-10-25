// style imports
import '../styles/login.css';
import '../styles/homepage.css';

const Login = () => {
  return (
    <div>
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
  );
}

export default Login;