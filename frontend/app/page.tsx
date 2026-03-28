import { Suspense } from "react";

import { ChatInterface } from "@/components/chat-interface";

export default function HomePage() {
  return (
    <Suspense>
      <ChatInterface />
    </Suspense>
  );
}
