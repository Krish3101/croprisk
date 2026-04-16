import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Bot, Loader, Send, User, X, MessageCircle } from 'lucide-react';

import { useSendMessage } from '../hooks/useApi';

const FloatingAssistant = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am your KisanAI assistant. How can I help you today?' }
    ]);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef(null);
    const sendMessageMutation = useSendMessage();

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        if (isOpen) scrollToBottom();
    }, [messages, isOpen, scrollToBottom]);

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
                content: response.answer || "I'm sorry, I couldn't process your request."
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
        <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 20, scale: 0.95 }}
                        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                        className="mb-4 w-80 sm:w-96 h-[500px] max-h-[80vh] flex flex-col glass rounded-2xl overflow-hidden shadow-2xl"
                    >
                        {/* Header */}
                        <div className="p-4 border-b border-white/20 bg-green-600/90 text-white flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-white/20 rounded-full">
                                    <Bot className="w-5 h-5" />
                                </div>
                                <div>
                                    <h2 className="font-semibold text-sm">KisanAI Assistant</h2>
                                    <p className="text-xs text-green-100">Online</p>
                                </div>
                            </div>
                            <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-white/20 rounded-lg transition-colors">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50 backdrop-blur-sm hide-scrollbar">
                            {messages.map((msg, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                                >
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'}`}>
                                        {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                                    </div>
                                    <div className={`max-w-[75%] p-3 rounded-2xl text-sm ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-tr-none'
                                        : 'bg-white border border-gray-100 text-gray-800 rounded-tl-none shadow-sm'
                                        }`}>
                                        <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                    </div>
                                </motion.div>
                            ))}

                            {sendMessageMutation.isPending && (
                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-2">
                                    <div className="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center">
                                        <Loader className="w-4 h-4 animate-spin" />
                                    </div>
                                </motion.div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area */}
                        <form onSubmit={handleSend} className="p-3 bg-white border-t border-gray-100">
                            <div className="flex gap-2 items-center bg-gray-50 rounded-full px-4 py-2 border border-gray-200 focus-within:ring-2 focus-within:ring-green-500/50 focus-within:border-green-500 transition-all">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Ask something..."
                                    className="flex-1 bg-transparent text-sm focus:outline-none"
                                    disabled={sendMessageMutation.isPending}
                                />
                                <button
                                    type="submit"
                                    disabled={sendMessageMutation.isPending || !input.trim()}
                                    className="text-green-600 disabled:opacity-50"
                                >
                                    <Send className="w-4 h-4" />
                                </button>
                            </div>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Floating Bubble Button */}
            {!isOpen && (
                <motion.button
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    whileHover={{ scale: 1.05 }}
                    onClick={() => setIsOpen(true)}
                    className="w-14 h-14 bg-gradient-to-tr from-green-600 to-green-400 text-white rounded-full shadow-xl shadow-green-600/30 flex items-center justify-center animate-float"
                >
                    <MessageCircle className="w-6 h-6" />
                </motion.button>
            )}
        </div>
    );
};

export default FloatingAssistant;
