const frame = document.querySelector("#serviceFrame");
const tabs = Array.from(document.querySelectorAll(".service-tab"));
const serviceTitle = document.querySelector("#serviceTitle");
const serviceDescription = document.querySelector("#serviceDescription");
const currentServiceName = document.querySelector("#currentServiceName");
const openExternal = document.querySelector("#openExternal");
const failureOpenExternal = document.querySelector("#failureOpenExternal");
const loadingState = document.querySelector("#loadingState");
const failureState = document.querySelector("#failureState");

let activeLoadToken = 0;
let loadTimer = null;

function setLoadingState(isLoading) {
  loadingState.hidden = !isLoading;
}

function showFailure(serviceUrl) {
  failureOpenExternal.href = serviceUrl;
  failureState.hidden = false;
}

function hideFailure() {
  failureState.hidden = true;
}

function armFrameTimeout(serviceUrl, token) {
  window.clearTimeout(loadTimer);
  loadTimer = window.setTimeout(() => {
    if (token === activeLoadToken) {
      setLoadingState(false);
      showFailure(serviceUrl);
    }
  }, 9000);
}

function activateService(tab) {
  const { serviceKey, serviceName, serviceDescription: description, serviceUrl } = tab.dataset;

  tabs.forEach((item) => {
    const isActive = item.dataset.serviceKey === serviceKey;
    item.classList.toggle("active", isActive);
    item.setAttribute("aria-selected", String(isActive));
  });

  serviceTitle.textContent = serviceName;
  currentServiceName.textContent = serviceName;
  serviceDescription.textContent = description;
  openExternal.href = serviceUrl;
  failureOpenExternal.href = serviceUrl;
  frame.title = serviceName;

  hideFailure();
  setLoadingState(true);
  activeLoadToken += 1;
  const token = activeLoadToken;
  armFrameTimeout(serviceUrl, token);

  if (frame.src !== serviceUrl) {
    frame.src = serviceUrl;
  }
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => activateService(tab));
});

frame.addEventListener("load", () => {
  window.clearTimeout(loadTimer);
  setLoadingState(false);
});

frame.addEventListener("error", () => {
  window.clearTimeout(loadTimer);
  setLoadingState(false);
  showFailure(frame.src);
});

if (tabs[0]) {
  armFrameTimeout(tabs[0].dataset.serviceUrl, activeLoadToken);
}
