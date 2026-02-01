import React from 'react';
import { Download, Calendar } from 'lucide-react';
import type { StudyPlan } from '../../types/study';

interface ExportICSProps {
  plan: StudyPlan;
}

export const ExportICS: React.FC<ExportICSProps> = ({ plan }) => {
  const generateICS = () => {
    const events = plan.tasks.map(task => {
      const start = new Date(task.scheduledDate);
      const end = new Date(start.getTime() + task.estimatedDuration * 60000);

      return `BEGIN:VEVENT
UID:${task.id}@aetios-med
DTSTAMP:${formatICSDate(new Date())}
DTSTART:${formatICSDate(start)}
DTEND:${formatICSDate(end)}
SUMMARY:Study: ${task.topicName}
DESCRIPTION:Type: ${task.type}\\nConfidence Goal: ${(task.confidenceGoal * 100).toFixed(0)}%
STATUS:${task.completed ? 'COMPLETED' : 'CONFIRMED'}
END:VEVENT`;
    }).join('\n');

    const ics = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Aetios-Med//Study Plan//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:${plan.name}
X-WR-TIMEZONE:UTC
${events}
END:VCALENDAR`;

    return ics;
  };

  const formatICSDate = (date: Date): string => {
    return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
  };

  const handleExport = () => {
    const ics = generateICS();
    const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${plan.name.replace(/\s+/g, '_')}.ics`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <button
      onClick={handleExport}
      className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center gap-2"
    >
      <Download size={18} />
      Export to Calendar (.ics)
    </button>
  );
};
