// Workflow Components
// This file exports all workflow management components for easy importing

// Legacy WebAwesome components (to be removed after complete migration)
export { WebAwesomeWorkflowDesigner } from './wa-workflow-designer.js';
export { WebAwesomeWorkflowDashboard } from './wa-workflow-dashboard.js';
export { WebAwesomeWorkflowExecutionDetail } from './wa-workflow-execution-detail.js';
export { WebAwesomeWorkflowSimulator } from './wa-workflow-simulator.js';

// OKUI components (migrated versions)
import './okui-workflow-dashboard.js';
import './okui-workflow-designer.js';
import './okui-workflow-execution-detail.js';
import './okui-workflow-simulator.js';