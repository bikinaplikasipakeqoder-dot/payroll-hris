'use client';

import { Employee } from '@/types';
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHeadCell } from '@/components/ui/Table';
import Badge from '@/components/ui/Badge';

interface EmployeeTableProps {
  employees: Employee[];
  onRowClick: (id: number) => void;
}

export default function EmployeeTable({ employees, onRowClick }: EmployeeTableProps) {
  if (employees.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        Belum ada data karyawan
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHeadCell>Kode</TableHeadCell>
          <TableHeadCell>Nama Lengkap</TableHeadCell>
          <TableHeadCell>Agama</TableHeadCell>
          <TableHeadCell>Department ID</TableHeadCell>
          <TableHeadCell>Posisi</TableHeadCell>
          <TableHeadCell>Status</TableHeadCell>
          <TableHeadCell>Aksi</TableHeadCell>
        </TableRow>
      </TableHeader>
      <TableBody>
        {employees.map((employee) => (
          <TableRow key={employee.id}>
            <TableCell>{employee.employee_code}</TableCell>
            <TableCell className="font-medium text-gray-900">
              {employee.full_name}
            </TableCell>
            <TableCell>{employee.religion ?? '-'}</TableCell>
            <TableCell>{employee.department_id ?? '-'}</TableCell>
            <TableCell>{employee.position_id ?? '-'}</TableCell>
            <TableCell>
              <Badge variant={employee.is_active ? 'success' : 'danger'}>
                {employee.is_active ? 'Aktif' : 'Nonaktif'}
              </Badge>
            </TableCell>
            <TableCell>
              <button
                onClick={() => onRowClick(employee.id)}
                className="text-primary-600 hover:text-primary-800 text-sm font-medium"
              >
                Lihat
              </button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
