/**
 * Messages
 *
 * Provides progressive enhancement for server-rendered Django messages
 * and allows dynamic creation of client-side messages.
 *
 * Based on the alerts system from squarelet/frontend/alerts.ts,
 * adapted for MuckRock's .message pattern.
 */

export type MessageType = "success" | "error" | "warning" | "info";

export interface MessageOptions {
  autoDismiss?: boolean;
  duration?: number;
}

const DEFAULT_OPTIONS: MessageOptions = {
  autoDismiss: true,
  duration: 5000,
};

// Store cleanup functions for each message element
const messageCleanups = new WeakMap<HTMLElement, () => void>();

/**
 * Initialize the message system by enhancing existing server-rendered
 * messages with auto-dismiss timers.
 */
export function initMessages(): void {
  const messages = document.querySelectorAll<HTMLElement>(".message");
  messages.forEach((messageElement) => {
    setupDismissButton(messageElement);
    if (messageElement.classList.contains("success")) {
      setupAutoDismiss(messageElement, DEFAULT_OPTIONS.duration!);
    }
  });
}

/**
 * Create and display a new message dynamically.
 *
 * @param text - The message to display
 * @param type - The message type (success, error, warning, info)
 * @param options - Optional configuration:
 *   - autoDismiss: Enable auto-dismiss timer (default: true)
 *   - duration: Auto-dismiss duration in ms (default: 5000)
 */
export function showMessage(
  text: string,
  type: MessageType = "info",
  options: MessageOptions = {},
): void {
  const opts = { ...DEFAULT_OPTIONS, ...options };

  let container = document.querySelector("ul.messages") as HTMLElement;
  if (!container) {
    container = document.createElement("ul");
    container.className = "messages nostyle";

    const header = document.querySelector(".header");
    if (header) {
      header.after(container);
    } else {
      document.querySelector(".content")?.prepend(container);
    }
  }

  const li = document.createElement("li");
  const messageElement = document.createElement("div");
  messageElement.className = `message ${type} message--fade-in`;

  const textSpan = document.createElement("span");
  textSpan.className = "text";
  textSpan.innerHTML = `<p>${text}</p>`;
  messageElement.appendChild(textSpan);

  setupDismissButton(messageElement);

  messageElement.addEventListener(
    "animationend",
    (e) => {
      if (
        (e.target as HTMLElement) === messageElement &&
        messageElement.classList.contains("message--fade-in")
      ) {
        messageElement.classList.remove("message--fade-in");
      }
    },
    { once: true },
  );

  li.appendChild(messageElement);
  container.appendChild(li);

  if (opts.autoDismiss && opts.duration) {
    setupAutoDismiss(messageElement, opts.duration);
  }
}

/**
 * Dismiss a message with animation.
 *
 * @param messageElement - The .message element to dismiss
 */
export function dismissMessage(messageElement: HTMLElement): void {
  const li = messageElement.parentElement;
  if (!li) return;

  const cleanup = messageCleanups.get(messageElement);
  if (cleanup) {
    cleanup();
    messageCleanups.delete(messageElement);
  }

  messageElement.classList.add("message--dismiss");

  messageElement.addEventListener(
    "animationend",
    () => {
      li.remove();

      const container = document.querySelector("ul.messages");
      if (container && container.children.length === 0) {
        container.remove();
      }
    },
    { once: true },
  );
}

/**
 * Set up the dismiss button for a message element.
 * Creates the button if it doesn't already exist (for dynamically created messages).
 */
function setupDismissButton(messageElement: HTMLElement): void {
  let button = messageElement.querySelector<HTMLButtonElement>("button.dismiss");
  if (!button) {
    button = document.createElement("button");
    button.className = "dismiss";
    button.setAttribute("aria-label", "Dismiss message");
    button.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="17" viewBox="0 0 16 17"><path fill-rule="evenodd" clip-rule="evenodd" d="M3.71983 4.22C3.86045 4.07955 4.05108 4.00066 4.24983 4.00066C4.44858 4.00066 4.6392 4.07955 4.77983 4.22L7.99983 7.44L11.2198 4.22C11.2885 4.14631 11.3713 4.08721 11.4633 4.04622C11.5553 4.00523 11.6546 3.98319 11.7553 3.98141C11.856 3.97963 11.956 3.99816 12.0494 4.03588C12.1428 4.0736 12.2276 4.12974 12.2988 4.20096C12.3701 4.27218 12.4262 4.35702 12.4639 4.4504C12.5016 4.54379 12.5202 4.64382 12.5184 4.74452C12.5166 4.84523 12.4946 4.94454 12.4536 5.03654C12.4126 5.12854 12.3535 5.21134 12.2798 5.28L9.05983 8.5L12.2798 11.72C12.3535 11.7887 12.4126 11.8715 12.4536 11.9635C12.4946 12.0555 12.5166 12.1548 12.5184 12.2555C12.5202 12.3562 12.5016 12.4562 12.4639 12.5496C12.4262 12.643 12.3701 12.7278 12.2988 12.799C12.2276 12.8703 12.1428 12.9264 12.0494 12.9641C11.956 13.0018 11.856 13.0204 11.7553 13.0186C11.6546 13.0168 11.5553 12.9948 11.4633 12.9538C11.3713 12.9128 11.2885 12.8537 11.2198 12.78L7.99983 9.56L4.77983 12.78C4.63765 12.9125 4.4496 12.9846 4.2553 12.9812C4.061 12.9777 3.87562 12.899 3.7382 12.7616C3.60079 12.6242 3.52208 12.4388 3.51865 12.2445C3.51522 12.0502 3.58735 11.8622 3.71983 11.72L6.93983 8.5L3.71983 5.28C3.57938 5.13938 3.50049 4.94875 3.50049 4.75C3.50049 4.55125 3.57938 4.36063 3.71983 4.22Z" /></svg>`;
    messageElement.appendChild(button);
  }
  button.addEventListener("click", () => dismissMessage(messageElement));
}

/**
 * Set up auto-dismiss for a message element.
 * Pauses on hover to allow reading.
 *
 * @param messageElement - The .message element
 * @param duration - Time in ms before auto-dismissing
 */
function setupAutoDismiss(messageElement: HTMLElement, duration: number): void {
  let timeoutId: number | null = null;
  let remainingTime = duration;
  let startTime = Date.now();

  const startTimer = () => {
    startTime = Date.now();
    timeoutId = window.setTimeout(() => {
      dismissMessage(messageElement);
    }, remainingTime);
  };

  const pauseTimer = () => {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
      remainingTime -= Date.now() - startTime;
      timeoutId = null;
    }
  };

  const resumeTimer = () => {
    if (remainingTime > 0) {
      startTimer();
    }
  };

  messageElement.addEventListener("mouseenter", pauseTimer);
  messageElement.addEventListener("mouseleave", resumeTimer);

  startTimer();

  messageCleanups.set(messageElement, () => {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
      timeoutId = null;
    }
    messageElement.removeEventListener("mouseenter", pauseTimer);
    messageElement.removeEventListener("mouseleave", resumeTimer);
  });
}
