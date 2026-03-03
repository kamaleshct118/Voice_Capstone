import { MessageSquare, Clock } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useLocation } from "react-router-dom";
import type { ChatMessage } from "@/types/clinical";
import { TOOL_LABELS } from "@/types/clinical";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

interface ChatSidebarProps {
  history: ChatMessage[];
  onSelect: (msg: ChatMessage) => void;
  activeId?: string;
}

const ChatSidebar = ({ history, onSelect, activeId }: ChatSidebarProps) => {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";

  return (
    <Sidebar collapsible="icon">
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>
            <MessageSquare className="w-4 h-4 mr-2" />
            {!collapsed && "Chat History"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {history.length === 0 && !collapsed && (
                <p className="px-3 py-4 text-xs text-muted-foreground text-center">
                  No conversations yet. Start by asking a question.
                </p>
              )}
              {history.map((msg) => (
                <SidebarMenuItem key={msg.id}>
                  <SidebarMenuButton
                    onClick={() => onSelect(msg)}
                    className={`w-full text-left ${activeId === msg.id ? "bg-muted text-primary font-medium" : ""}`}
                  >
                    <MessageSquare className="w-4 h-4 shrink-0" />
                    {!collapsed && (
                      <div className="flex-1 min-w-0">
                        <p className="text-sm truncate">{msg.query}</p>
                        <p className="text-[10px] text-muted-foreground flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          <span className="ml-1 px-1 py-0.5 rounded bg-primary/10 text-primary">
                            {TOOL_LABELS[msg.response.tool_type] || msg.response.tool_type}
                          </span>
                        </p>
                      </div>
                    )}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
};

export default ChatSidebar;
