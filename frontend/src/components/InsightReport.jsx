import { useMemo } from 'react';
import { AlertCircle, CloudRain } from 'lucide-react';

const InsightReport = ({ insight }) => {
    const { summaryLine, riskLines, weatherLines } = useMemo(() => {
        if (!insight) {
            return { summaryLine: null, riskLines: [], weatherLines: [] };
        }
        const lines = insight.split('\n').filter(line => line.trim());
        const summaryLine = lines.find(line => line.includes('Summary:') || !line.includes(':'));
        const riskLines = lines.filter(line => line.toLowerCase().includes('risk'));
        const weatherLines = lines.filter(line => line.toLowerCase().includes('weather') || line.toLowerCase().includes('suggest'));
        return { summaryLine, riskLines, weatherLines };
    }, [insight]);

    if (!summaryLine && riskLines.length === 0 && weatherLines.length === 0) {
        return (
            <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-700 whitespace-pre-line">{insight}</p>
            </div>
        );
    }

    return (
        <>
            {summaryLine && (
                <div className="p-4 bg-purple-50 rounded-lg">
                    <p className="text-gray-700">
                        {summaryLine.replace('Summary:', '').trim()}
                    </p>
                </div>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {riskLines.length > 0 && (
                    <div className="p-4 bg-orange-50 rounded-lg border border-orange-100">
                        <div className="flex items-center gap-2 mb-2">
                            <AlertCircle className="w-4 h-4 text-orange-600" />
                            <h4 className="font-medium text-orange-900">Crop Risks</h4>
                        </div>
                        <ul className="space-y-1 text-sm text-orange-800">
                            {riskLines.map((line, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                    <span className="text-orange-400 mt-1">•</span>
                                    <span>{line.replace(/.*risk[s]?:?/i, '').trim()}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
                
                {weatherLines.length > 0 && (
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                        <div className="flex items-center gap-2 mb-2">
                            <CloudRain className="w-4 h-4 text-blue-600" />
                            <h4 className="font-medium text-blue-900">Weather Suggestions</h4>
                        </div>
                        <ul className="space-y-1 text-sm text-blue-800">
                            {weatherLines.map((line, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                    <span className="text-blue-400 mt-1">•</span>
                                    <span>{line.replace(/.*suggest[ion]*[s]?:?/i, '').trim()}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </>
    );
};

export default InsightReport;
