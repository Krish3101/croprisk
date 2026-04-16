import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Bot, Loader, Send, User } from 'lucide-react';

import PageTransition from '../components/PageTransition';
import { useSendMessage } from '../hooks/useApi';

const Chat = () => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am your KisanAI assistant. How can I help you with your farming today?' }
    ]);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef(null);
    const sendMessageMutation = useSendMessage();

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, scrollToBottom]);

    const handleSend = useCallback(async (e) => {
        e.preventDefault();
        if (!input.trim() || sendMessageMutation.isPending) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');

        try {
            const response = await sendMessageMutation.mutateAsync({
                question: userMessage.content
            });

            const botMessage = {
                role: 'assistant',
                content: response.answer || "I'm sorry, I couldn't process that request."
            };

            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            const errorMessage = error?.detail || error?.message || "I'm having trouble connecting to the server.";
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: errorMessage
            }]);
        }
    }, [input, sendMessageMutation]);

    return (
        <PageTransition>
            <div className="h-[calc(100vh-8rem)] flex flex-col bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                {/* Chat Header */}
                <div className="p-4 border-b border-gray-100 bg-green-50 flex items-center gap-3">
                    <div className="p-2 bg-green-600 rounded-full text-white">
                        <Bot className="w-5 h-5" />
                    </div>
                    <div>
                        <h2 className="font-semibold text-gray-900">KisanAI Assistant</h2>
                        <p className="text-xs text-green-700">Always here to help</p>
                    </div>
                </div>

                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    <AnimatePresence initial={false}>
                        {messages.map((msg, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                transition={{ duration: 0.2 }}
                                className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                            >
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'
                                    }`}>
                                    {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                                </div>

                                <div className={`max-w-[80%] p-3 rounded-2xl ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-tr-none'
                                    : 'bg-gray-100 text-gray-800 rounded-tl-none'
                                    }`}>
                                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {sendMessageMutation.isPending && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex gap-3"
                        >
                            <div className="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center flex-shrink-0">
                                <Bot className="w-5 h-5" />
                            </div>
                            <div className="bg-gray-100 p-3 rounded-2xl rounded-tl-none flex items-center gap-2">
                                <Loader className="w-4 h-4 animate-spin text-gray-500" />
                                <span className="text-sm text-gray-500">Thinking...</span>
                            </div>
                        </motion.div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <form onSubmit={handleSend} className="p-4 border-t border-gray-100 bg-gray-50">
                    <div className="flex gap-2">
                        <input
                            id="chat-input"
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask about crops, weather, or farming tips..."
                            className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
                            disabled={sendMessageMutation.isPending}
                            autoComplete="off"
                            aria-label="Chat message input"
                        />
                        <button
                            type="submit"
                            disabled={sendMessageMutation.isPending || !input.trim()}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            aria-label="Send message"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </div>
                </form>
            </div>
        </PageTransition>
    );
};

export default Chat;
