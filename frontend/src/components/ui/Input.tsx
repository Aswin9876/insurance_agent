interface Props extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

export function Input({ label, error, hint, id, ...props }: Props) {
  const inputId = id || label.toLowerCase().replace(/[^a-z]+/g, "_");
  return (
    <div className="w-full">
      <label htmlFor={inputId} className="mb-1 block text-sm font-medium text-slate-700">
        {label} {props.required && <span className="text-red-500">*</span>}
      </label>
      <input
        id={inputId}
        className={`w-full rounded-lg border px-3 py-2 text-sm outline-none transition
          focus:ring-2 focus:ring-indigo-500 disabled:bg-slate-100
          ${error ? "border-red-400 focus:ring-red-400" : "border-slate-300"}`}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
      {!error && hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "children"> {
  label: string;
  error?: string;
  options: Array<{ value: string; label: string }>;
}

export function Select({ label, error, options, id, ...props }: SelectProps) {
  const inputId = id || label.toLowerCase().replace(/[^a-z]+/g, "_");
  return (
    <div className="w-full">
      <label htmlFor={inputId} className="mb-1 block text-sm font-medium text-slate-700">
        {label} {props.required && <span className="text-red-500">*</span>}
      </label>
      <select
        id={inputId}
        className={`w-full rounded-lg border px-3 py-2 text-sm outline-none transition
          focus:ring-2 focus:ring-indigo-500 bg-white
          ${error ? "border-red-400" : "border-slate-300"}`}
        {...props}
      >
        <option value="">Select…</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}