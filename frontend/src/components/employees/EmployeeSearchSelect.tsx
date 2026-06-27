'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Search, User, X } from 'lucide-react';

interface Employee {
  id: number;
  first_name: string;
  last_name: string | null;
  employee_code: string;
}

interface EmployeeSearchSelectProps {
  employees: Employee[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  label?: string;
}

export function EmployeeSearchSelect({
  employees,
  value,
  onChange,
  placeholder = 'Ketik ID, nama, atau kode karyawan...',
  disabled = false,
  label = 'Karyawan',
}: EmployeeSearchSelectProps) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedEmployee = useMemo(
    () => employees.find((e) => String(e.id) === value),
    [employees, value]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return employees;
    return employees.filter((emp) => {
      const text = `${emp.employee_code} ${emp.first_name} ${emp.last_name || ''} ${emp.id}`.toLowerCase();
      return text.includes(q);
    });
  }, [employees, query]);

  useEffect(() => {
    setHighlightedIndex(0);
  }, [filtered]);

  useEffect(() => {
    if (selectedEmployee) {
      setQuery(`${selectedEmployee.first_name} ${selectedEmployee.last_name || ''} (${selectedEmployee.employee_code})`);
    } else {
      setQuery('');
    }
  }, [selectedEmployee]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        if (selectedEmployee) {
          setQuery(`${selectedEmployee.first_name} ${selectedEmployee.last_name || ''} (${selectedEmployee.employee_code})`);
        } else {
          setQuery('');
        }
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [selectedEmployee]);

  const handleSelect = (employee: Employee) => {
    onChange(String(employee.id));
    setQuery(`${employee.first_name} ${employee.last_name || ''} (${employee.employee_code})`);
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev + 1) % filtered.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev - 1 + filtered.length) % filtered.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const emp = filtered[highlightedIndex];
      if (emp) handleSelect(emp);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const clearSelection = () => {
    onChange('');
    setQuery('');
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      )}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-gray-400" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
            if (selectedEmployee && e.target.value !== `${selectedEmployee.first_name} ${selectedEmployee.last_name || ''} (${selectedEmployee.employee_code})`) {
              onChange('');
            }
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          className="w-full pl-9 pr-9 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:text-gray-500"
        />
        {value && (
          <button
            type="button"
            onClick={clearSelection}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {isOpen && filtered.length > 0 && (
        <div className="absolute z-50 mt-1 w-full max-h-60 overflow-auto bg-white border border-gray-200 rounded-lg shadow-lg">
          {filtered.map((emp, index) => (
            <button
              key={emp.id}
              type="button"
              onClick={() => handleSelect(emp)}
              onMouseEnter={() => setHighlightedIndex(index)}
              className={`w-full text-left px-3 py-2 flex items-center gap-2 text-sm hover:bg-indigo-50 ${
                index === highlightedIndex ? 'bg-indigo-50' : ''
              }`}
            >
              <User className="h-4 w-4 text-gray-400 flex-shrink-0" />
              <div className="min-w-0">
                <p className="font-medium text-gray-900 truncate">
                  {emp.first_name} {emp.last_name || ''}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  ID: {emp.id} · {emp.employee_code}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}

      {isOpen && query && filtered.length === 0 && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm text-gray-500">
          Tidak ada karyawan yang cocok.
        </div>
      )}
    </div>
  );
}
