"""
Browser enhancement scripts for Playwright automation.

This module contains JavaScript injection scripts that enhance browser capabilities:
- Anti-detection measures
- DOM monitoring and hooks
- Dynamic content loading detection
- Scroll and interaction utilities
- Performance monitoring
"""

# ===========================
# Anti-Detection Scripts
# ===========================

ANTI_DETECTION_SCRIPT = """
// Hide webdriver property to bypass anti-bot detection
Object.defineProperty(Object.getPrototypeOf(navigator), 'webdriver', {
    set: undefined,
    enumerable: true,
    configurable: true,
    get: new Proxy(
        Object.getOwnPropertyDescriptor(Object.getPrototypeOf(navigator), 'webdriver').get,
        {
            apply: (target, thisArg, args) => {
                // Emulate getter call validation
                Reflect.apply(target, thisArg, args);
                return false;
            }
        }
    )
});

// Fake chrome object for better anti-detection
window.chrome = window.chrome || { runtime: {} };

// Fake plugins for better anti-detection
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// Fake languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});
"""

# ===========================
# DOM Monitoring Scripts
# ===========================

HACKED_CREATE_ELEMENT = """
// Track DOM element creation for monitoring dynamic content
window.elementsCreatedByDOM = [];

document._createElement = document.createElement;
document.createElement = function (name) {
   var ele = document._createElement(name);
   window.elementsCreatedByDOM.push(ele);
   return ele;
}
"""

HACKED_ATTACH_SHADOW = """
// Replace shadow DOM with regular div for better content extraction
Element.prototype._attachShadow = Element.prototype.attachShadow;
Element.prototype.attachShadow = function() {
    const shadowDiv = document.createElement('div');
    this.appendChild(shadowDiv);
    return shadowDiv;
};
"""

CREATE_HOOKED_ELEMENT = """
// Create hidden input elements as hooks for load detection
window._hooked = [];
window.createHidden = function(name) {
    if (!window._hooked.includes(name)) {
        window._hooked.push(name);
    }
    let inputId = 'pw-tider';
    if (name != "") {
        inputId = `pw-tider-${name}`;
    }
    let inputElement = document.querySelector('input#' + inputId);
    if (inputElement !== null && inputId !== 'pw-tider') {
        return;
    }
    let newInput = document.createElement('input');
    newInput.id = inputId;
    newInput.type = 'hidden';
    newInput.value = 'DOM_LOAD_HOOK';
    let lastElement = (document?.body || document?.head || document).lastElementChild;
    if (lastElement) {
        lastElement.insertAdjacentElement('afterend', newInput);
    }
}
"""

# ===========================
# Utility Functions
# ===========================

UTILITY_FUNCTIONS = """
// Delay utility function
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Wait utility function
window.wait = async function(seconds) {
    console.log(`Starting to wait for ${seconds} seconds...`);
    await delay(seconds * 1000);
    console.log(`${seconds} seconds have passed!`);
    return "Completed";
};

// Get CSS selector for any element
function getCssSelector(element) {
    if (!(element instanceof Element)) {
        return null;
    }

    let selector = '';
    while (element) {
        if (element.tagName) {
            let selectorPart = element.tagName.toLowerCase();
            if (element.id) {
                selectorPart += '#' + element.id;
                selector = selectorPart + (selector ? ' > ' + selector : '');
                break;
            }
            if (element.className) {
                const classNames = element.className.split(' ');
                for (const className of classNames) {
                    if (className) {
                        selectorPart += '.' + className;
                    }
                }
            }
            let parentElement = element.parentElement;
            if (parentElement) {
                let index = Array.prototype.indexOf.call(parentElement.children, element);
                if (index && element.tagName) {
                    index = index + 1;
                    selectorPart += ":nth-child(" + index.toString() + ")";
                }
            }
            selector = selectorPart + (selector ? ' > ' + selector : '');
        }
        element = element.parentNode;
    }
    return selector;
}
"""

# ===========================
# Resource and Loading Detection
# ===========================

RESOURCE_MONITORING = """
// Monitor resource loading status
function getResourceStats() {
    return window.performance.getEntries("resource") || [];
}

let lastResources = getResourceStats();

window.checkResourcesDone = function () {
    let resources = getResourceStats();
    if (resources.length != lastResources.length) {
        lastResources = getResourceStats();
        return false;
    }
    else if (resources.length > 0 && resources[resources.length - 1].name != lastResources[lastResources.length - 1].name) {
        lastResources = getResourceStats();
        return false;
    }
    else if (resources.length > 0 && resources[resources.length - 1].duration != lastResources[lastResources.length - 1].duration) {
        lastResources = getResourceStats();
        return false;
    }
    else {
        return true;
    }
}

// Get all network requests
window.getNetworkRequests = function() {
    const entries = performance.getEntriesByType("resource");
    return entries.map(entry => ({
        name: entry.name,
        type: entry.initiatorType,
        duration: entry.duration,
        size: entry.transferSize,
        startTime: entry.startTime
    }));
}
"""

# ===========================
# Interaction Detection
# ===========================

INTERACTION_DETECTION = """
// Find all clickable span elements
window.getSpansWithClick = function () {
    const allElements = document.querySelectorAll('span');
    const spans = [];

    allElements.forEach(element => {
        if (element.onclick) {
            spans.push(getCssSelector(element));
        }
    });
    return spans;
}

// Find all interactive elements
window.getInteractiveElements = function() {
    const selectors = 'button, a, input, select, textarea, [onclick], [role="button"]';
    const elements = document.querySelectorAll(selectors);
    return Array.from(elements).map(el => ({
        tag: el.tagName.toLowerCase(),
        selector: getCssSelector(el),
        text: el.textContent?.trim().substring(0, 50) || '',
        visible: el.offsetParent !== null
    }));
}
"""

# ===========================
# Performance Monitoring
# ===========================

PERFORMANCE_MONITORING = """
// Get page performance metrics
window.getPerformanceMetrics = function() {
    const perfData = performance.getEntriesByType('navigation')[0];
    if (!perfData) return null;

    return {
        dns: perfData.domainLookupEnd - perfData.domainLookupStart,
        tcp: perfData.connectEnd - perfData.connectStart,
        request: perfData.responseStart - perfData.requestStart,
        response: perfData.responseEnd - perfData.responseStart,
        domProcessing: perfData.domComplete - perfData.domInteractive,
        loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
        totalTime: perfData.loadEventEnd - perfData.fetchStart
    };
}

// Get page size metrics
window.getPageSize = function() {
    return {
        scrollHeight: document.documentElement.scrollHeight,
        scrollWidth: document.documentElement.scrollWidth,
        clientHeight: document.documentElement.clientHeight,
        clientWidth: document.documentElement.clientWidth,
        bodyHeight: document.body.scrollHeight,
        bodyWidth: document.body.scrollWidth
    };
}
"""

# ===========================
# Style Manipulation
# ===========================

STYLE_PATCH = """
// Remove body height/width constraints for full page capture
(() => {
    const styleSheets = document.styleSheets;
    for (let i = 0; i < styleSheets.length; i++) {
        try {
            const rules = styleSheets[i].cssRules;
            for (let j = 0; j < rules.length; j++) {
                if (rules[j].selectorText === 'body') {
                    rules[j].style.height = '';
                    rules[j].style.width = '';
                }
            }
        } catch (e) {
            // Some style sheets may not be accessible due to cross-domain
        }
    }

    document.body.style.removeProperty('height');
    document.body.style.removeProperty('width');

    document.documentElement.style.height = 'auto';
    document.documentElement.style.width = 'auto';
    document.body.style.height = 'auto';
    document.body.style.width = 'auto';
    document.body.style.overflow = 'visible';
})();
"""

# ===========================
# Complete Initialization Script
# ===========================

COMPLETE_INIT_SCRIPT = (
    ANTI_DETECTION_SCRIPT +
    "\n\n" + HACKED_CREATE_ELEMENT +
    "\n\n" + HACKED_ATTACH_SHADOW +
    "\n\n" + CREATE_HOOKED_ELEMENT +
    "\n\n" + UTILITY_FUNCTIONS +
    "\n\n" + RESOURCE_MONITORING +
    "\n\n" + INTERACTION_DETECTION +
    "\n\n" + PERFORMANCE_MONITORING
)

# ===========================
# Dynamic Load Hooks
# ===========================

def get_vue_dom_load_hook(script_name: str) -> str:
    """
    Generate a hook script for Vue.js applications.

    Args:
        script_name: Name identifier for the script being hooked

    Returns:
        JavaScript code to inject after script execution
    """
    return f"""
(this || window).wait(0.5).then(result => {{
    console.log('Hook completed for: {script_name}');
}});

setTimeout((this || window).createHidden("{script_name}"), 100);
"""

LAST_SCRIPT = """setTimeout(window.createHidden(""), 100);"""

DOM_LOAD_HOOK = f"""
const pwTiderScript = document.createElement('script');
pwTiderScript.textContent = '{LAST_SCRIPT}';
const lastElement = (document?.body || document?.head || document).lastElementChild;
if (lastElement) {{
    lastElement.insertAdjacentElement('afterend', pwTiderScript);
}} else {{
    (document?.body || document?.head || document).appendChild(pwTiderScript);
}}
"""

# ===========================
# Configuration
# ===========================

class BrowserScriptConfig:
    """Configuration for browser script injection"""

    # Enable/disable specific features
    ENABLE_ANTI_DETECTION = True
    ENABLE_DOM_MONITORING = True
    ENABLE_RESOURCE_MONITORING = True
    ENABLE_INTERACTION_DETECTION = True
    ENABLE_PERFORMANCE_MONITORING = True

    # Timing configuration
    HOOK_TIMEOUT_MS = 30000  # 30 seconds
    HOOK_CHECK_INTERVAL_MS = 100

    # Hook element identifier prefix
    HOOK_ELEMENT_PREFIX = "pw-tider"

    @classmethod
    def get_init_script(cls) -> str:
        """Get the complete initialization script based on config"""
        scripts = []

        if cls.ENABLE_ANTI_DETECTION:
            scripts.append(ANTI_DETECTION_SCRIPT)

        if cls.ENABLE_DOM_MONITORING:
            scripts.extend([
                HACKED_CREATE_ELEMENT,
                HACKED_ATTACH_SHADOW,
                CREATE_HOOKED_ELEMENT
            ])

        scripts.append(UTILITY_FUNCTIONS)

        if cls.ENABLE_RESOURCE_MONITORING:
            scripts.append(RESOURCE_MONITORING)

        if cls.ENABLE_INTERACTION_DETECTION:
            scripts.append(INTERACTION_DETECTION)

        if cls.ENABLE_PERFORMANCE_MONITORING:
            scripts.append(PERFORMANCE_MONITORING)

        return "\n\n".join(scripts)


# Export commonly used scripts
__all__ = [
    'COMPLETE_INIT_SCRIPT',
    'ANTI_DETECTION_SCRIPT',
    'RESOURCE_MONITORING',
    'INTERACTION_DETECTION',
    'PERFORMANCE_MONITORING',
    'STYLE_PATCH',
    'DOM_LOAD_HOOK',
    'get_vue_dom_load_hook',
    'BrowserScriptConfig',
]
