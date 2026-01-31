/**
 * Chat Component
 * Handles messaging between investors and startups with file sharing and read receipts
 */
import { useState, useEffect, useRef } from "react";
import {
  Send,
  MessageSquare,
  X,
  Upload,
  Check,
  CheckCheck,
  Download,
} from "lucide-react";
import toast from "react-hot-toast";

export default function Chat({
  investorId,
  startupId,
  currentUserId,
  onClose,
}) {
  const [conversation, setConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (investorId && startupId) {
      initializeConversation();
    }
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [investorId, startupId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const initializeConversation = async () => {
    try {
      setLoading(true);

      // Create or get conversation
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const convResponse = await fetch(
        `${apiUrl}/api/conversations?investor_id=${investorId}&startup_id=${startupId}`,
        { method: "POST" }
      );

      if (!convResponse.ok) {
        throw new Error("Failed to create conversation");
      }

      const convData = await convResponse.json();
      setConversation(convData);

      // Load messages
      await loadMessages(convData.id);

      // Connect to WebSocket for real-time updates
      connectWebSocket(convData.id);
    } catch (error) {
      console.error("Error initializing conversation:", error);
      toast.error("Failed to initialize chat");
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (conversationId) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/conversations/${conversationId}/messages`
      );

      if (response.ok) {
        const data = await response.json();
        setMessages(data);

        // Mark messages as read
        if (data.length > 0) {
          await fetch(
            `${apiUrl}/api/conversations/${conversationId}/read-all?user_id=${currentUserId}`,
            { method: "PUT" }
          );
        }
      }
    } catch (error) {
      console.error("Error loading messages:", error);
    }
  };

  const connectWebSocket = (conversationId) => {
    // WebSocket connection for real-time messaging
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const wsProtocol = apiUrl.startsWith("https") ? "wss:" : "ws:";
    const wsHost = apiUrl.replace(/^https?:\/\//, "").replace(/^wss?:\/\//, "");
    const wsUrl = `${wsProtocol}//${wsHost}/ws/${conversationId}/${currentUserId}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("WebSocket connected");
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "new_message") {
          setMessages((prev) => [...prev, data.message]);
          scrollToBottom();

          // Mark as read if it's not from current user
          if (data.message.sender_id !== currentUserId) {
            const apiUrl =
              process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";
            fetch(`${apiUrl}/api/messages/${data.message.id}/read`, {
              method: "PUT",
            });
          }
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (conversationId) {
            connectWebSocket(conversationId);
          }
        }, 3000);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Failed to connect WebSocket:", error);
      // Fallback to polling if WebSocket fails
      startPolling(conversationId);
    }
  };

  const startPolling = (conversationId) => {
    // Fallback: poll for new messages every 3 seconds
    const pollInterval = setInterval(async () => {
      if (conversationId) {
        await loadMessages(conversationId);
      }
    }, 3000);

    return () => clearInterval(pollInterval);
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !conversation) return;

    try {
      setSending(true);
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000";

      const response = await fetch(`${apiUrl}/api/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          conversation_id: conversation.id,
          sender_id: currentUserId,
          content: newMessage.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      const messageData = await response.json();
      setMessages((prev) => [...prev, messageData]);
      setNewMessage("");
      scrollToBottom();
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !conversation) return;

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      toast.error("File size must be less than 10MB");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      return;
    }

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'image/jpeg',
      'image/jpg',
      'image/png',
      'image/gif',
      'image/webp'
    ];
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|doc|docx|jpg|jpeg|png|gif|webp)$/i)) {
      toast.error("File type not supported. Please upload PDF, DOC, DOCX, or image files.");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      return;
    }

    try {
      setUploadingFile(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      const formData = new FormData();
      formData.append("file", file);
      formData.append("conversation_id", conversation.id.toString());
      formData.append("sender_id", currentUserId.toString());
      formData.append("message_content", newMessage.trim() || "");

      const response = await fetch(`${apiUrl}/api/messages/file-upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to upload file");
      }

      const messageData = await response.json();
      setMessages((prev) => [...prev, messageData]);
      setNewMessage("");
      scrollToBottom();
      toast.success("File shared successfully!");

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      toast.error(error.message || "Failed to share file");
    } finally {
      setUploadingFile(false);
    }
  };

  const markMessageAsRead = async (messageId) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      await fetch(`${apiUrl}/api/messages/${messageId}/read`, {
        method: "PUT",
      });
    } catch (error) {
      console.error("Error marking message as read:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">Failed to initialize chat</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-blue-600" />
          <div>
            <h3 className="font-semibold">
              {currentUserId === investorId
                ? conversation.startup_name
                : conversation.investor_name}
            </h3>
            <p className="text-xs text-gray-500">
              {currentUserId === investorId ? "Startup" : "Investor"}
            </p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          messages.map((message) => {
            const isOwnMessage = message.sender_id === currentUserId;
            const fileSize = message.file_size
              ? (message.file_size / 1024).toFixed(2)
              : 0;

            return (
              <div
                key={message.id}
                className={`flex ${
                  isOwnMessage ? "justify-end" : "justify-start"
                } group`}
                onMouseEnter={() =>
                  !isOwnMessage &&
                  !message.read &&
                  markMessageAsRead(message.id)
                }
              >
                <div
                  className={`max-w-xs lg:max-w-md rounded-lg ${
                    isOwnMessage
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-800"
                  }`}
                >
                  {!isOwnMessage && (
                    <p className="text-xs font-semibold px-4 pt-2 pb-0 opacity-75">
                      {message.sender_name}
                    </p>
                  )}

                  <div className="px-4 py-2">
                    <p className="text-sm whitespace-pre-wrap">
                      {message.content}
                    </p>

                    {/* File Attachment */}
                    {message.file_url && (() => {
                      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
                      const fullFileUrl = message.file_url.startsWith('http') 
                        ? message.file_url 
                        : `${apiUrl}${message.file_url}`;
                      const isImage = message.file_type?.startsWith('image/') || 
                        /\.(jpg|jpeg|png|gif|webp)$/i.test(message.file_name || '');
                      
                      return (
                        <div className="mt-3">
                          {isImage ? (
                            // Image preview
                            <div className="rounded-lg overflow-hidden">
                              <a
                                href={fullFileUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block"
                              >
                                <img
                                  src={fullFileUrl}
                                  alt={message.file_name}
                                  className="max-w-full h-auto rounded-lg cursor-pointer hover:opacity-90 transition"
                                  onError={(e) => {
                                    // Fallback if image fails to load
                                    e.target.style.display = 'none';
                                    e.target.nextSibling.style.display = 'block';
                                  }}
                                />
                              </a>
                              <div
                                className={`p-3 rounded-lg flex items-center justify-between ${
                                  isOwnMessage ? "bg-blue-500" : "bg-gray-300"
                                }`}
                                style={{ display: 'none' }}
                              >
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                  <Upload className="w-4 h-4 flex-shrink-0" />
                                  <div className="min-w-0 flex-1">
                                    <p className="text-xs font-semibold truncate">
                                      {message.file_name}
                                    </p>
                                    <p className="text-xs opacity-75">{fileSize} KB</p>
                                  </div>
                                </div>
                                <a
                                  href={fullFileUrl}
                                  download
                                  className={`flex-shrink-0 p-2 rounded hover:opacity-80 transition ml-2 ${
                                    isOwnMessage
                                      ? "bg-blue-500 text-white"
                                      : "bg-gray-400 text-gray-800"
                                  }`}
                                >
                                  <Download className="w-4 h-4" />
                                </a>
                              </div>
                            </div>
                          ) : (
                            // File download button
                            <div
                              className={`p-3 rounded-lg flex items-center justify-between ${
                          isOwnMessage ? "bg-blue-500" : "bg-gray-300"
                        }`}
                      >
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <Upload className="w-4 h-4 flex-shrink-0" />
                          <div className="min-w-0 flex-1">
                            <p className="text-xs font-semibold truncate">
                              {message.file_name}
                            </p>
                            <p className="text-xs opacity-75">{fileSize} KB</p>
                          </div>
                        </div>
                        <a
                                href={`${apiUrl}/api/messages/file/${message.id}`}
                                download={message.file_name}
                                target="_blank"
                                rel="noopener noreferrer"
                          className={`flex-shrink-0 p-2 rounded hover:opacity-80 transition ml-2 ${
                            isOwnMessage
                              ? "bg-blue-500 text-white"
                              : "bg-gray-400 text-gray-800"
                          }`}
                        >
                          <Download className="w-4 h-4" />
                        </a>
                      </div>
                    )}
                        </div>
                      );
                    })()}
                  </div>

                  <div
                    className={`px-4 pb-2 text-xs flex items-center justify-between ${
                      isOwnMessage ? "text-blue-100" : "text-gray-500"
                    }`}
                  >
                    <span>
                      {new Date(message.created_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>

                    {/* Read Receipt */}
                    {isOwnMessage && (
                      <span className="ml-2 flex items-center gap-1">
                        {message.read ? (
                          <>
                            <CheckCheck className="w-3 h-3" />
                            {message.read_at && (
                              <span className="text-xs opacity-75">
                                {new Date(message.read_at).toLocaleTimeString(
                                  [],
                                  {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                  }
                                )}
                              </span>
                            )}
                          </>
                        ) : (
                          <Check className="w-3 h-3 opacity-50" />
                        )}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t bg-gray-50">
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.webp"
            onChange={handleFileSelect}
            disabled={uploadingFile || sending}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadingFile || sending}
            title="Share a file"
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            {uploadingFile && <span className="text-xs">Uploading...</span>}
          </button>
          <textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={2}
            disabled={sending || uploadingFile}
          />
          <button
            onClick={sendMessage}
            disabled={!newMessage.trim() || sending || uploadingFile}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
