-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 23, 2025 at 08:28 PM
-- Server version: 10.6.19-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `mediclinic`
--

-- --------------------------------------------------------

--
-- Table structure for table `appointments`
--

CREATE TABLE `appointments` (
  `id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `doctor_id` int(11) NOT NULL,
  `appointment_date` date NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `status` varchar(20) DEFAULT 'booked',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `cancellation_reason` text DEFAULT NULL,
  `doctor_notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `appointments`
--

INSERT INTO `appointments` (`id`, `patient_id`, `doctor_id`, `appointment_date`, `start_time`, `end_time`, `status`, `created_at`, `cancellation_reason`, `doctor_notes`) VALUES
(8, 2, 2, '2025-04-23', '16:00:00', '17:00:00', 'completed', '2025-04-23 05:36:31', NULL, 'I have seen the patient. They have a severe headache. Asked to book an appointment again for next week. ');

-- --------------------------------------------------------

--
-- Table structure for table `doctor_availability`
--

CREATE TABLE `doctor_availability` (
  `id` int(11) NOT NULL,
  `doctor_id` int(11) NOT NULL,
  `day_of_week` enum('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `slot_duration` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `doctor_availability`
--

INSERT INTO `doctor_availability` (`id`, `doctor_id`, `day_of_week`, `start_time`, `end_time`, `slot_duration`) VALUES
(13, 2, 'Monday', '09:00:00', '12:00:00', 30),
(14, 2, 'Tuesday', '09:00:00', '12:00:00', 30),
(15, 2, 'Wednesday', '12:00:00', '17:00:00', 60);

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL,
  `receiver_id` int(11) NOT NULL,
  `sender_role` enum('Doctor','Patient','OfficeManager') NOT NULL,
  `receiver_role` enum('Doctor','Patient','OfficeManager') NOT NULL,
  `message` text NOT NULL,
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`id`, `sender_id`, `receiver_id`, `sender_role`, `receiver_role`, `message`, `is_read`, `created_at`) VALUES
(6, 2, 2, 'Patient', 'Doctor', 'New appointment booked by Sandhya Raavi on 2025-04-23 from 16:00:00 to 17:00:00.', 0, '2025-04-23 05:36:31'),
(7, 2, 2, 'Doctor', 'Patient', 'Your appointment on 2025-04-23 at 16:00:00 was approved.', 0, '2025-04-23 05:37:39');

-- --------------------------------------------------------

--
-- Table structure for table `patients`
--

CREATE TABLE `patients` (
  `id` int(11) NOT NULL,
  `firstname` varchar(50) NOT NULL,
  `lastname` varchar(50) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `patients`
--

INSERT INTO `patients` (`id`, `firstname`, `lastname`, `phone`, `email`, `password_hash`) VALUES
(2, 'Sandhya', 'Raavi', '33565676988', 'sandhya@gmail.com', 'scrypt:32768:8:1$SjCIMGt8FIq9Iu2X$8148ffa4bbb6d80fbf6e1f10b1029f9676b5967129b37bde740046dcdd9a2b3f33b2f3f46070a19401396434c57fbe38ae1e739da5c54d023dd1ecc141976204'),
(3, 'Sandiiz', 'Raaviz', '55544575767889', 'sandiiz@gmail.com', 'scrypt:32768:8:1$hJZGyDCLP8gxsdbc$10bc14ca7a034e1a4376c9618d58967be0e74c1ca100e50716f9414c6812aea7760821d2b9d9d66420099c955fc0b1a9fce00c75b38e15a497822a1ae0a888b7');

-- --------------------------------------------------------

--
-- Table structure for table `staff`
--

CREATE TABLE `staff` (
  `id` int(11) NOT NULL,
  `firstname` varchar(50) DEFAULT NULL,
  `lastname` varchar(50) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `password_hash` varchar(255) DEFAULT NULL,
  `role` enum('Doctor','Office Manager') NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `specialization` varchar(100) DEFAULT NULL,
  `status` varchar(255) NOT NULL DEFAULT 'active',
  `availability` varchar(255) NOT NULL DEFAULT 'available'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `staff`
--

INSERT INTO `staff` (`id`, `firstname`, `lastname`, `phone`, `email`, `password_hash`, `role`, `created_at`, `specialization`, `status`, `availability`) VALUES
(1, 'Vishnu', 'Prakash', '23456789765', 'vishnu@gmail.com', 'scrypt:32768:8:1$GGgFC3mKcEg0ccQI$d4eb59bfdc46df55b6b6405876c1fafd7f30b462017176167e04bfa08ea5ba91125ed6f427999ab3766e6bf62dc267bcc9708f246de22f47a2fbbd7e17215791', 'Office Manager', '2025-04-11 06:50:17', NULL, 'active', ''),
(2, 'Sandya', 'Raaviz', '6466478489787', 'doctorraavi@gmail.com', 'scrypt:32768:8:1$aJbYDcZLiXAx16qa$3e3193ec88ad42c85eacd32a429100df60d0ad548dc13f16081cb41b3ce44f678b06193378ac4ed4bc1fcaa9f2def7cebde0bd34be593774dd7ecdde8cf5ba14', 'Doctor', '2025-04-11 08:52:57', 'General Consultation', 'active', 'available'),
(5, 'Vinay', 'Vardhan', '4632343455', 'vinay@gmail.com', 'scrypt:32768:8:1$tk6svIZVsILo3yM6$992bea702c7538b306e3ede582dad8148df2ebbab219cd415696149bc0a3544ceaf1c25eed83be9c1c4d74183375a9c4b147077da40463a8e52447d120f4d2fd', 'Doctor', '2025-04-21 15:36:40', 'Chronic Diseases', 'active', 'available');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `appointments`
--
ALTER TABLE `appointments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `patient_id` (`patient_id`),
  ADD KEY `doctor_id` (`doctor_id`);

--
-- Indexes for table `doctor_availability`
--
ALTER TABLE `doctor_availability`
  ADD PRIMARY KEY (`id`),
  ADD KEY `doctor_id` (`doctor_id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `patients`
--
ALTER TABLE `patients`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `phone` (`phone`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `staff`
--
ALTER TABLE `staff`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `appointments`
--
ALTER TABLE `appointments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `doctor_availability`
--
ALTER TABLE `doctor_availability`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `patients`
--
ALTER TABLE `patients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `staff`
--
ALTER TABLE `staff`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `appointments`
--
ALTER TABLE `appointments`
  ADD CONSTRAINT `appointments_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`),
  ADD CONSTRAINT `appointments_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `staff` (`id`);

--
-- Constraints for table `doctor_availability`
--
ALTER TABLE `doctor_availability`
  ADD CONSTRAINT `doctor_availability_ibfk_1` FOREIGN KEY (`doctor_id`) REFERENCES `staff` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
