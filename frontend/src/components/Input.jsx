/**
 * Reusable Input component with consistent styling
 * @param {Object} props
 * @param {string} props.label - Input label
 * @param {string} props.error - Error message
 * @param {string} props.type - Input type (text, number, email, etc.)
 * @param {boolean} props.required - Required field indicator
 * @param {string} props.placeholder - Placeholder text
 * @param {React.ReactNode} props.icon - Icon component (from lucide-react)
 */
export default function Input({
  label,
  error,
  type = 'text',
  required = false,
  placeholder,
  icon,
  className = '',
  ...props
}) {
  const Icon = icon;

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1.5">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Icon size={18} className="text-gray-400" />
          </div>
        )}
        <input
          type={type}
          placeholder={placeholder}
          className={`
            w-full rounded-lg border-2 transition-colors duration-200
            ${Icon ? 'pl-10' : 'pl-3'} pr-3 py-2
            ${error 
              ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
              : 'border-gray-300 focus:border-green-500 focus:ring-green-500'
            }
            focus:outline-none focus:ring-2
            disabled:bg-gray-100 disabled:cursor-not-allowed
          `}
          {...props}
        />
      </div>
      {error && (
        <p className="mt-1.5 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
