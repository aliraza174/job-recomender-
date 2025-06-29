% job(JobID, Title, Field, Skills, Qualification, City, Salary)

job(j1, 'Software Engineer', it, ['Python', 'Java'], bachelors, karachi, 120000).
job(j2, 'Web Developer', it, ['HTML', 'CSS', 'JavaScript'], bachelors, lahore, 80000).
job(j3, 'Data Analyst', it, ['Python', 'SQL'], masters, islamabad, 130000).
job(j4, 'Accountant', finance, ['Excel', 'Accounting'], bachelors, karachi, 80000).
job(j5, 'Teacher', education, ['Communication', 'Subject Knowledge'], masters, lahore, 80000).
job(j6, 'Mobile App Developer', it, ['Flutter', 'React Native'], bachelors, lahore, 90000).
job(j7, 'Graphic Designer', design, ['Photoshop', 'Illustrator'], bachelors, multan, 75000).
job(j8, 'HR Executive', hr, ['Recruitment', 'Communication'], bachelors, islamabad, 80000).
job(j9, 'SEO Specialist', marketing, ['SEO', 'Content Writing'], bachelors, karachi, 80000).
job(j10, 'Project Manager', management, ['Leadership', 'Planning'], masters, lahore, 140000).

% available_in(JobID, [Cities])

available_in(j1, [karachi, lahore]).
available_in(j2, [lahore, islamabad]).
available_in(j3, [islamabad]).
available_in(j4, [karachi]).
available_in(j5, [lahore, multan]).
available_in(j6, [lahore, karachi]).
available_in(j7, [multan, lahore]).
available_in(j8, [islamabad, lahore]).
available_in(j9, [karachi, islamabad]).
available_in(j10, [lahore, multan]).
