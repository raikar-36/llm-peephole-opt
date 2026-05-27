define i32 @chain_lshr_shl_1_1(i32 %x) {
entry:
  %tmp = lshr i32 %x, 1
  %result = shl i32 %tmp, 1
  ret i32 %result
}
