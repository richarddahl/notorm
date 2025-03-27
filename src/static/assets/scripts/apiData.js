let accessToken;
const authenticationUrl = "/api/auth/login";

document.addEventListener("ok-prompt-login", function () {
  document.querySelector("ok-login-form-dialog").showDialog();
});

export const login = async function (formData) {
  try {
    const response = await fetch(authenticationUrl, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      return false;
    }
    accessToken = data.access_token;
    if (window.PasswordCredential) {
      let cred = new PasswordCredential({
        id: formData.get("username"),
        password: formData.get("password"),
      });
      navigator.credentials.store(cred);
    }
    document.querySelector("ok-base").logged_in = true;
    return true;
  } catch (error) {
    console.log(error);
    return false;
  }
};

export const haveToken = function () {
  if (accessToken) {
    return true;
  }
  return false;
};

export const getData = async function (url) {
  return fetch(url, { headers: { Authorization: `Bearer ${accessToken}` } })
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        if (response.status === 401) {
          throw new Error("Invalid username or password");
        } else {
          throw new Error("Something went wrong");
        }
      }
    })
    .catch((error) => {
      console.log(error);
    });
};

export const postData = async function (url, formData) {
  return fetch(url, {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        if (response.status === 401) {
          throw new Error("Invalid username or password");
        } else {
          throw new Error("Something went wrong");
        }
      }
    })
    .catch((error) => {
      console.log(error);
    });
};
