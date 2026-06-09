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
let activeServiceKey = tabs[0]?.dataset.serviceKey || "";

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

async function fetchLaunch(serviceKey) {
  const response = await fetch(`/api/services/${encodeURIComponent(serviceKey)}/launch`, {
    credentials: "same-origin",
  });

  if (!response.ok) {
    throw new Error(`launch request failed: ${response.status}`);
  }

  return response.json();
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

async function activateService(tab) {
  const { serviceKey, serviceName, serviceDescription: description, serviceUrl } = tab.dataset;
  activeServiceKey = serviceKey;

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

  try {
    const launch = await fetchLaunch(serviceKey);
    if (token !== activeLoadToken) {
      return;
    }

    openExternal.href = launch.externalUrl || serviceUrl;
    failureOpenExternal.href = launch.externalUrl || serviceUrl;

    if (frame.src !== launch.launchUrl) {
      frame.src = launch.launchUrl;
    }
  } catch (_error) {
    if (token !== activeLoadToken) {
      return;
    }
    setLoadingState(false);
    showFailure(serviceUrl);
  }
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    activateService(tab).catch(() => {
      showFailure(tab.dataset.serviceUrl);
    });
  });
});

async function openCurrentServiceInNewWindow(event) {
  event.preventDefault();

  if (!activeServiceKey) {
    return;
  }

  try {
    const launch = await fetchLaunch(activeServiceKey);
    window.open(launch.externalUrl || launch.launchUrl, "_blank", "noopener,noreferrer");
  } catch (_error) {
    window.open(openExternal.href, "_blank", "noopener,noreferrer");
  }
}

openExternal.addEventListener("click", openCurrentServiceInNewWindow);
failureOpenExternal.addEventListener("click", openCurrentServiceInNewWindow);

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
  activateService(tabs[0]).catch(() => {
    showFailure(tabs[0].dataset.serviceUrl);
  });
}
