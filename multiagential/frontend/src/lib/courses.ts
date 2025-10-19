export interface Course {
  id: string;
  title: string;
  description: string;
  category: 'ai-ml' | 'data-science' | 'software-eng' | 'cybersecurity' | 'blockchain' | 'cloud' | 'quantum';
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration: string;
  modules: CourseModule[];
  tags: string[];
  marketValue: 'high' | 'very-high' | 'extremely-high';
  avgSalary: string;
  jobGrowth: string;
  prerequisites: string[];
  icon: string;
}

export interface CourseModule {
  id: string;
  title: string;
  description: string;
  estimatedTime: string;
  topics: string[];
  completed?: boolean;
}

export const COURSE_DATA: Course[] = [
  {
    id: 'machine-learning-systems',
    title: 'Production Machine Learning Systems',
    description: 'Build and deploy scalable ML systems that actually work in production environments.',
    category: 'ai-ml',
    difficulty: 'advanced',
    duration: '12 weeks',
    marketValue: 'extremely-high',
    avgSalary: '$150k-250k',
    jobGrowth: '+22% (much faster than average)',
    prerequisites: ['Python', 'Statistics', 'Linear Algebra'],
    icon: '🤖',
    tags: ['MLOps', 'TensorFlow', 'PyTorch', 'Docker', 'Kubernetes', 'AWS'],
    modules: [
      {
        id: 'ml-fundamentals',
        title: 'ML Engineering Fundamentals',
        description: 'Core concepts for building production ML systems',
        estimatedTime: '2 weeks',
        topics: ['Model Architecture', 'Data Pipelines', 'Feature Engineering', 'Model Versioning']
      },
      {
        id: 'deployment-strategies',
        title: 'Deployment & Scaling',
        description: 'Get your models into production and keep them running',
        estimatedTime: '3 weeks',
        topics: ['Container Orchestration', 'A/B Testing', 'Model Monitoring', 'Auto-scaling']
      },
      {
        id: 'mlops-practices',
        title: 'MLOps Best Practices',
        description: 'Industry-standard practices for ML operations',
        estimatedTime: '2 weeks',
        topics: ['CI/CD for ML', 'Data Versioning', 'Experiment Tracking', 'Model Governance']
      }
    ]
  },
  {
    id: 'advanced-data-engineering',
    title: 'Large-Scale Data Engineering',
    description: 'Design data systems that handle billions of records without breaking a sweat.',
    category: 'data-science',
    difficulty: 'advanced',
    duration: '10 weeks',
    marketValue: 'very-high',
    avgSalary: '$130k-200k',
    jobGrowth: '+8% (faster than average)',
    prerequisites: ['SQL', 'Python', 'Distributed Systems'],
    icon: '📊',
    tags: ['Apache Spark', 'Kafka', 'Airflow', 'Snowflake', 'dbt', 'Apache Iceberg'],
    modules: [
      {
        id: 'data-architecture',
        title: 'Modern Data Architecture',
        description: 'Design systems that scale from GB to PB',
        estimatedTime: '2 weeks',
        topics: ['Data Lakes vs Warehouses', 'Lambda Architecture', 'Streaming vs Batch', 'Data Mesh']
      },
      {
        id: 'streaming-systems',
        title: 'Real-time Data Processing',
        description: 'Handle data as it flows, not after it sits',
        estimatedTime: '3 weeks',
        topics: ['Apache Kafka', 'Stream Processing', 'Event-Driven Architecture', 'Change Data Capture']
      },
      {
        id: 'data-quality',
        title: 'Data Quality & Governance',
        description: 'Keep your data clean and trustworthy',
        estimatedTime: '2 weeks',
        topics: ['Data Testing', 'Schema Evolution', 'Data Lineage', 'Privacy Engineering']
      }
    ]
  },
  {
    id: 'cloud-native-architecture',
    title: 'Cloud-Native System Design',
    description: 'Build systems that were born in the cloud and love it there.',
    category: 'software-eng',
    difficulty: 'advanced',
    duration: '14 weeks',
    marketValue: 'extremely-high',
    avgSalary: '$140k-220k',
    jobGrowth: '+15% (much faster than average)',
    prerequisites: ['Distributed Systems', 'Containerization', 'API Design'],
    icon: '☁️',
    tags: ['Kubernetes', 'Microservices', 'Service Mesh', 'Observability', 'Terraform'],
    modules: [
      {
        id: 'microservices-design',
        title: 'Microservices Architecture',
        description: 'Break down monoliths without breaking your sanity',
        estimatedTime: '3 weeks',
        topics: ['Service Decomposition', 'API Gateway', 'Inter-service Communication', 'Circuit Breakers']
      },
      {
        id: 'kubernetes-mastery',
        title: 'Kubernetes in Production',
        description: 'Orchestrate containers like a pro',
        estimatedTime: '4 weeks',
        topics: ['Pod Management', 'Service Discovery', 'Ingress Controllers', 'Custom Resources']
      },
      {
        id: 'observability',
        title: 'System Observability',
        description: 'Know what your system is doing when things go wrong',
        estimatedTime: '2 weeks',
        topics: ['Distributed Tracing', 'Metrics & Alerting', 'Log Aggregation', 'SLI/SLO Design']
      }
    ]
  },
  {
    id: 'advanced-cybersecurity',
    title: 'Enterprise Security Engineering',
    description: 'Protect systems from threats you haven\'t even thought of yet.',
    category: 'cybersecurity',
    difficulty: 'advanced',
    duration: '16 weeks',
    marketValue: 'extremely-high',
    avgSalary: '$120k-180k',
    jobGrowth: '+35% (much faster than average)',
    prerequisites: ['Network Security', 'Cryptography', 'System Administration'],
    icon: '🛡️',
    tags: ['Zero Trust', 'SIEM', 'Threat Hunting', 'DevSecOps', 'Cloud Security'],
    modules: [
      {
        id: 'threat-modeling',
        title: 'Advanced Threat Modeling',
        description: 'Think like an attacker to defend better',
        estimatedTime: '3 weeks',
        topics: ['Attack Surface Analysis', 'STRIDE Methodology', 'Risk Assessment', 'Security Architecture']
      },
      {
        id: 'zero-trust',
        title: 'Zero Trust Architecture',
        description: 'Never trust, always verify - even your own network',
        estimatedTime: '4 weeks',
        topics: ['Identity Management', 'Micro-segmentation', 'Continuous Verification', 'Policy Enforcement']
      },
      {
        id: 'incident-response',
        title: 'Security Incident Response',
        description: 'When (not if) things go wrong, be ready',
        estimatedTime: '3 weeks',
        topics: ['Forensics', 'Malware Analysis', 'Recovery Procedures', 'Post-incident Analysis']
      }
    ]
  },
  {
    id: 'blockchain-development',
    title: 'Enterprise Blockchain Development',
    description: 'Build decentralized systems that actually solve real problems.',
    category: 'blockchain',
    difficulty: 'advanced',
    duration: '12 weeks',
    marketValue: 'very-high',
    avgSalary: '$110k-170k',
    jobGrowth: '+8% (as fast as average)',
    prerequisites: ['Smart Contracts', 'Cryptography', 'Distributed Systems'],
    icon: '⛓️',
    tags: ['Ethereum', 'Solidity', 'Web3', 'DeFi', 'Layer 2', 'Consensus Algorithms'],
    modules: [
      {
        id: 'smart-contract-security',
        title: 'Smart Contract Security',
        description: 'Write contracts that don\'t lose millions of dollars',
        estimatedTime: '3 weeks',
        topics: ['Common Vulnerabilities', 'Formal Verification', 'Audit Practices', 'Gas Optimization']
      },
      {
        id: 'defi-protocols',
        title: 'DeFi Protocol Development',
        description: 'Build the financial infrastructure of the future',
        estimatedTime: '4 weeks',
        topics: ['AMM Design', 'Yield Farming', 'Governance Tokens', 'Cross-chain Bridges']
      },
      {
        id: 'scaling-solutions',
        title: 'Blockchain Scaling',
        description: 'Make blockchain fast enough for real-world use',
        estimatedTime: '2 weeks',
        topics: ['Layer 2 Solutions', 'State Channels', 'Sidechains', 'Sharding']
      }
    ]
  },
  {
    id: 'quantum-computing',
    title: 'Quantum Computing Applications',
    description: 'Get ahead of the curve with quantum algorithms and applications.',
    category: 'quantum',
    difficulty: 'advanced',
    duration: '20 weeks',
    marketValue: 'extremely-high',
    avgSalary: '$130k-250k',
    jobGrowth: '+50% (emerging field)',
    prerequisites: ['Linear Algebra', 'Complex Numbers', 'Python', 'Quantum Mechanics Basics'],
    icon: '⚛️',
    tags: ['Qiskit', 'Quantum Algorithms', 'NISQ', 'Quantum ML', 'Quantum Cryptography'],
    modules: [
      {
        id: 'quantum-algorithms',
        title: 'Quantum Algorithm Design',
        description: 'Algorithms that leverage quantum weirdness for speed',
        estimatedTime: '5 weeks',
        topics: ['Shor\'s Algorithm', 'Grover\'s Algorithm', 'Variational Quantum Eigensolver', 'QAOA']
      },
      {
        id: 'quantum-ml',
        title: 'Quantum Machine Learning',
        description: 'Where quantum computing meets AI',
        estimatedTime: '4 weeks',
        topics: ['Quantum Neural Networks', 'Quantum Feature Maps', 'Quantum Advantage in ML', 'Hybrid Algorithms']
      },
      {
        id: 'quantum-applications',
        title: 'Real-world Quantum Applications',
        description: 'Solving actual problems with quantum computers',
        estimatedTime: '4 weeks',
        topics: ['Drug Discovery', 'Portfolio Optimization', 'Cryptography', 'Materials Science']
      }
    ]
  }
];

export class CourseManager {
  private static PROGRESS_KEY = 'courseProgress';
  private static ENROLLED_KEY = 'enrolledCourses';

  static getEnrolledCourses(): string[] {
    if (typeof window === 'undefined') return [];
    const stored = localStorage.getItem(this.ENROLLED_KEY);
    return stored ? JSON.parse(stored) : [];
  }

  static enrollInCourse(courseId: string) {
    if (typeof window === 'undefined') return;
    const enrolled = this.getEnrolledCourses();
    if (!enrolled.includes(courseId)) {
      enrolled.push(courseId);
      localStorage.setItem(this.ENROLLED_KEY, JSON.stringify(enrolled));
    }
  }

  static getCourseProgress(courseId: string): Record<string, boolean> {
    if (typeof window === 'undefined') return {};
    const stored = localStorage.getItem(`${this.PROGRESS_KEY}_${courseId}`);
    return stored ? JSON.parse(stored) : {};
  }

  static updateModuleProgress(courseId: string, moduleId: string, completed: boolean) {
    if (typeof window === 'undefined') return;
    const progress = this.getCourseProgress(courseId);
    progress[moduleId] = completed;
    localStorage.setItem(`${this.PROGRESS_KEY}_${courseId}`, JSON.stringify(progress));
  }

  static getRecommendedCourses(limit: number = 3): Course[] {
    // Simple recommendation logic - can be enhanced with user preferences
    return COURSE_DATA
      .filter(course => course.marketValue === 'extremely-high')
      .slice(0, limit);
  }

  static getCoursesByCategory(category: Course['category']): Course[] {
    return COURSE_DATA.filter(course => course.category === category);
  }

  static searchCourses(query: string): Course[] {
    const searchTerm = query.toLowerCase();
    return COURSE_DATA.filter(course => 
      course.title.toLowerCase().includes(searchTerm) ||
      course.description.toLowerCase().includes(searchTerm) ||
      course.tags.some(tag => tag.toLowerCase().includes(searchTerm))
    );
  }
}