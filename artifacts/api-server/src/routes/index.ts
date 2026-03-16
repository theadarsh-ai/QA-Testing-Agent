import { Router, type IRouter } from "express";
import healthRouter from "./health";
import designguardRouter from "./designguard/index";

const router: IRouter = Router();

router.use(healthRouter);
router.use(designguardRouter);

export default router;
