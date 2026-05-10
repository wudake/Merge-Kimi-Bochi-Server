/*
  Warnings:

  - You are about to drop the column `difficulty` on the `topics` table. All the data in the column will be lost.
  - You are about to drop the column `estimated_effect` on the `topics` table. All the data in the column will be lost.
  - You are about to drop the column `platforms` on the `topics` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "topics" DROP COLUMN "difficulty",
DROP COLUMN "estimated_effect",
DROP COLUMN "platforms",
ADD COLUMN     "completed_at" TIMESTAMP(3),
ADD COLUMN     "is_completed" BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN     "operator_id" TEXT,
ADD COLUMN     "published_accounts" TEXT;
