import { Header } from "@/components/Header";
import { Wizard } from "@/components/Wizard";
import { ChatAssistant } from "@/components/assistant/ChatAssistant";

export default function Home() {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <Wizard />
      </main>
      <ChatAssistant />
    </div>
  );
}