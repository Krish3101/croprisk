
export const SkeletonCard = () => (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 animate-pulse">
        <div className="flex items-center justify-between mb-4">
            <div className="h-5 bg-gray-200 rounded w-24"></div>
            <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
        </div>
        <div className="space-y-3">
            <div className="h-8 bg-gray-200 rounded w-32"></div>
            <div className="h-4 bg-gray-200 rounded w-48"></div>
            <div className="h-4 bg-gray-200 rounded w-40"></div>
        </div>
    </div>
);

export const SkeletonList = ({ count = 3 }) => (
    <div className="space-y-4">
        {Array.from({ length: count }).map((_, i) => (
            <div key={i} className="bg-white p-4 rounded-xl border border-gray-100 animate-pulse">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
                    <div className="flex-1 space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                </div>
            </div>
        ))}
    </div>
);

export const SkeletonTable = ({ rows = 5 }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-48"></div>
        </div>
        <div className="divide-y divide-gray-100">
            {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="p-4 flex items-center justify-between animate-pulse">
                    <div className="flex items-center gap-4 flex-1">
                        <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
                        <div className="space-y-2 flex-1">
                            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                            <div className="h-3 bg-gray-200 rounded w-1/4"></div>
                        </div>
                    </div>
                    <div className="h-8 bg-gray-200 rounded w-24"></div>
                </div>
            ))}
        </div>
    </div>
);

export const SkeletonDashboard = () => (
    <div className="space-y-8">
        <div className="bg-gradient-to-r from-gray-200 to-gray-300 rounded-2xl p-8 h-32 animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
        </div>
    </div>
);
