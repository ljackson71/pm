import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "@/components/App";
import { initialData } from "@/lib/kanban";

vi.mock("@/lib/api", () => ({
  getBoard: vi.fn(async () => initialData),
  saveBoard: vi.fn(),
}));

const mockFetch = (statusFor: (url: string) => number) => {
  const fetchMock = vi.fn(
    async (url: string) => new Response("{}", { status: statusFor(url) })
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
};

const signIn = async (password: string) => {
  await userEvent.type(await screen.findByLabelText("Username"), "user");
  await userEvent.type(screen.getByLabelText("Password"), password);
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("renders the login form when not signed in", async () => {
    mockFetch(() => 401);
    render(<App />);
    expect(await screen.findByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("submits credentials to the login endpoint", async () => {
    const fetchMock = mockFetch((url) => (url === "/api/login" ? 200 : 401));
    render(<App />);
    await signIn("password");
    expect(fetchMock).toHaveBeenCalledWith("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "user", password: "password" }),
    });
  });

  it("shows an error on 401", async () => {
    mockFetch(() => 401);
    render(<App />);
    await signIn("wrong");
    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid/i);
  });

  it("shows the board on success", async () => {
    mockFetch((url) => (url === "/api/login" ? 200 : 401));
    render(<App />);
    await signIn("password");
    expect(
      await screen.findByRole("heading", { name: "Kanban Studio" })
    ).toBeInTheDocument();
  });
});
